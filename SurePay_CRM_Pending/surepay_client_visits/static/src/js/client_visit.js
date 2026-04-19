/** @odoo-module **/
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { _t } from '@web/core/l10n/translation';

export class LocationCaptureService {
    constructor(env, rpc, notification) {
        this.env = env;
        this.rpc = rpc;
        this.notification = notification;
    }

    async captureLocation(model, resId) {
        if (!navigator.geolocation) {
            this.notification.add(_t('Geolocation is not supported by your browser.'), {
                type: 'danger',
            });
            return;
        }

        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0,
                });
            });

            const coordinates = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
            };

            console.log('Coordinates captured:', coordinates);

            if (resId) {
                // Record exists, update it directly
                try {
                    await this.rpc('/web/dataset/call_kw/surepay.client.visit/write', {
                        model: 'surepay.client.visit',
                        method: 'write',
                        args: [[resId], {
                            latitude: coordinates.latitude,
                            longitude: coordinates.longitude,
                        }],
                        kwargs: {
                            context: {
                                from_location_capture: true
                            }
                        },
                    });
                    console.log('Coordinates saved permanently for record:', resId);
                    
                    // Trigger form reload to update the map display
                    this.reloadFormWithCoordinates(resId, coordinates);
                    
                } catch (error) {
                    console.error('Failed to save coordinates permanently:', error);
                    throw error;
                }
            } else {
                // For new records, we need to save the coordinates to the form
                // so they get saved when the record is created
                this.tempCoordinates = coordinates;
                console.log('Coordinates stored temporarily for new record:', this.tempCoordinates);
                
                // Try to save coordinates to the unsaved form
                await this.saveCoordinatesToUnsavedForm(coordinates);
                
                // Update the form with temporary coordinates
                this.updateFormWithTempCoordinates(coordinates);
            }
        } catch (error) {
            console.error('Geolocation error:', error);
            this.notification.add(_t('Failed to get your location. Please check your browser permissions.'), {
                type: 'danger',
            });
            throw error;
        }
    }

    async saveCoordinatesToUnsavedForm(coordinates) {
        try {
            // Try to find the form view and update the model values
            // This will ensure coordinates are saved when the form is submitted
            
            // Update the form fields
            this.updateFormFields(coordinates);
            
            // Try to trigger a form change event to let Odoo know the form has been modified
            const form = document.querySelector('.o_form_view');
            if (form) {
                // Trigger change event on the form
                form.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Try to find and click the save button if it exists
                const saveButton = document.querySelector('.o_form_button_save');
                if (saveButton) {
                    // Enable save button if it's disabled
                    saveButton.disabled = false;
                    saveButton.classList.remove('disabled');
                    
                    // Show notification to user to save the form
                    this.notification.add(_t('Location captured! Please save the form to store the coordinates permanently.'), {
                        type: 'info',
                        sticky: true,
                    });
                }
                
                // Try to find the Odoo form controller and mark it as dirty
                try {
                    const formController = this.env.services.ui.activeController;
                    if (formController && formController.model) {
                        // Try to update the model directly
                        const currentData = formController.model.data;
                        if (currentData) {
                            // Update the model data
                            Object.assign(currentData, {
                                latitude: coordinates.latitude,
                                longitude: coordinates.longitude,
                                temp_latitude: coordinates.latitude,
                                temp_longitude: coordinates.longitude
                            });
                            
                            // Mark the model as dirty
                            if (formController.model.__isDirty) {
                                formController.model.__isDirty = true;
                            }
                            
                            // Trigger model change event
                            formController.model.notify();
                            
                            console.log('Form model updated with coordinates');
                        }
                    }
                } catch (modelError) {
                    console.warn('Could not update form model directly:', modelError);
                }
            }
            
            console.log('Coordinates saved to unsaved form');
        } catch (error) {
            console.warn('Could not save coordinates to unsaved form:', error);
        }
    }

    updateFormWithTempCoordinates(coordinates) {
        // Update form fields with temporary coordinates
        this.updateFormFields(coordinates);
        
        // Try to update the map display
        setTimeout(() => {
            try {
                const mapService = this.env.services.visitMapEmbed;
                if (mapService) {
                    mapService.updateMapWithCoordinates(coordinates.latitude, coordinates.longitude)
                        .then(() => {
                            console.log('Map updated with temporary coordinates');
                        })
                        .catch(error => {
                            console.warn('Failed to update map with temporary coordinates:', error);
                        });
                }
            } catch (error) {
                console.warn('Error updating map with temporary coordinates:', error);
            }
        }, 200);
    }

    reloadFormWithCoordinates(resId, coordinates) {
        // Trigger form reload to update map display
        setTimeout(() => {
            try {
                // Update the map iframe directly
                const mapService = this.env.services.visitMapEmbed;
                if (mapService) {
                    mapService.updateMapWithCoordinates(coordinates.latitude, coordinates.longitude)
                        .then(() => {
                            console.log('Map updated successfully');
                        })
                        .catch(error => {
                            console.warn('Failed to update map:', error);
                        });
                }
                
                // Update form fields if they exist
                this.updateFormFields(coordinates);
                
            } catch (error) {
                console.warn('Error during form reload:', error);
            }
        }, 500); // Small delay to ensure database update is complete
    }

    updateFormFields(coordinates) {
        try {
            // Enhanced field selectors for Odoo 17
            const fieldSelectors = [
                // Try multiple selector strategies
                `input[name="latitude"]`,
                `input[data-name="latitude"]`,
                `.o_field_widget[name="latitude"] input`,
                `.o_field_float[name="latitude"] input`,
                `div[name="latitude"] input`,
                // More specific selectors
                `.o_form_view input[name="latitude"]`,
                `.o_form_sheet_bg input[name="latitude"]`
            ];
            
            const lonFieldSelectors = [
                `input[name="longitude"]`,
                `input[data-name="longitude"]`,
                `.o_field_widget[name="longitude"] input`,
                `.o_field_float[name="longitude"] input`,
                `div[name="longitude"] input`,
                `.o_form_view input[name="longitude"]`,
                `.o_form_sheet_bg input[name="longitude"]`
            ];
            
            // Update latitude field
            let latField = null;
            for (const selector of fieldSelectors) {
                latField = document.querySelector(selector);
                if (latField) {
                    console.log('Found latitude field with selector:', selector);
                    break;
                }
            }
            
            if (latField) {
                // Store original value for comparison
                const originalValue = latField.value;
                latField.value = coordinates.latitude;
                
                // Trigger comprehensive events for Odoo 17
                const events = ['input', 'change', 'blur', 'keyup', 'keydown'];
                events.forEach(eventName => {
                    latField.dispatchEvent(new Event(eventName, { bubbles: true, cancelable: true }));
                });
                
                // Also trigger custom events that Odoo might listen for
                latField.dispatchEvent(new Event('odoo_field_change', { bubbles: true }));
                
                console.log('Latitude field updated:', coordinates.latitude, 'Field value after update:', latField.value);
            } else {
                console.warn('Latitude field not found with any selector');
            }
            
            // Update longitude field
            let lonField = null;
            for (const selector of lonFieldSelectors) {
                lonField = document.querySelector(selector);
                if (lonField) {
                    console.log('Found longitude field with selector:', selector);
                    break;
                }
            }
            
            if (lonField) {
                // Store original value for comparison
                const originalValue = lonField.value;
                lonField.value = coordinates.longitude;
                
                // Trigger comprehensive events for Odoo 17
                const events = ['input', 'change', 'blur', 'keyup', 'keydown'];
                events.forEach(eventName => {
                    lonField.dispatchEvent(new Event(eventName, { bubbles: true, cancelable: true }));
                });
                
                // Also trigger custom events that Odoo might listen for
                lonField.dispatchEvent(new Event('odoo_field_change', { bubbles: true }));
                
                console.log('Longitude field updated:', coordinates.longitude, 'Field value after update:', lonField.value);
            } else {
                console.warn('Longitude field not found with any selector');
            }
            
            // Update temporary latitude field
            const tempLatField = document.querySelector('input[name="temp_latitude"]') || 
                               document.querySelector('input[data-name="temp_latitude"]');
            if (tempLatField) {
                tempLatField.value = coordinates.latitude;
                tempLatField.dispatchEvent(new Event('change', { bubbles: true }));
                tempLatField.dispatchEvent(new Event('input', { bubbles: true }));
                console.log('Temporary latitude field updated:', coordinates.latitude);
            }
            
            // Update temporary longitude field
            const tempLonField = document.querySelector('input[name="temp_longitude"]') || 
                               document.querySelector('input[data-name="temp_longitude"]');
            if (tempLonField) {
                tempLonField.value = coordinates.longitude;
                tempLonField.dispatchEvent(new Event('change', { bubbles: true }));
                tempLonField.dispatchEvent(new Event('input', { bubbles: true }));
                console.log('Temporary longitude field updated:', coordinates.longitude);
            }
            
            console.log('Form fields updated with coordinates:', coordinates);
            
            // Additional: Try to update the form model directly if available
            this.updateFormModel(coordinates);
            
            // Try to trigger form dirty state
            this.triggerFormDirtyState();
            
        } catch (error) {
            console.warn('Could not update form fields:', error);
        }
    }
    
    updateFormModel(coordinates) {
        try {
            // Try to access the Odoo form model directly
            const formView = document.querySelector('.o_form_view');
            if (formView && formView.__owl__) {
                // Odoo 17 uses OWL framework, try to access the component
                const component = formView.__owl__.component;
                if (component && component.props && component.props.record) {
                    const record = component.props.record;
                    if (record.update) {
                        // Update the record data
                        record.update({
                            latitude: coordinates.latitude,
                            longitude: coordinates.longitude,
                            temp_latitude: coordinates.latitude,
                            temp_longitude: coordinates.longitude
                        });
                        console.log('Form model updated via OWL component');
                    }
                }
            }
            
            // Additional approach: Try to find the field widgets and update them directly
            this.updateFieldWidgets(coordinates);
            
            // Try to access the form service and update the model
            try {
                const formService = this.env.services.ui.activeController;
                if (formService && formService.model) {
                    const model = formService.model;
                    if (model.data) {
                        // Update the model data directly
                        Object.assign(model.data, {
                            latitude: coordinates.latitude,
                            longitude: coordinates.longitude,
                            temp_latitude: coordinates.latitude,
                            temp_longitude: coordinates.longitude
                        });
                        
                        // Trigger model change
                        if (model.notify) {
                            model.notify();
                        }
                        
                        // Mark as dirty
                        if (typeof model.__isDirty !== 'undefined') {
                            model.__isDirty = true;
                        }
                        
                        console.log('Form model updated via service');
                    }
                }
            } catch (serviceError) {
                console.warn('Could not update form model via service:', serviceError);
            }
            
        } catch (error) {
            console.warn('Could not update form model:', error);
        }
    }
    
    updateFieldWidgets(coordinates) {
        try {
            // Try to find and update field widgets directly
            const latWidget = document.querySelector('.o_field_widget[name="latitude"]');
            const lonWidget = document.querySelector('.o_field_widget[name="longitude"]');
            
            if (latWidget && latWidget.__owl__) {
                const latComponent = latWidget.__owl__.component;
                if (latComponent && latComponent.props && latComponent.props.record) {
                    latComponent.props.record.update({ latitude: coordinates.latitude });
                    console.log('Latitude widget updated via OWL');
                }
            }
            
            if (lonWidget && lonWidget.__owl__) {
                const lonComponent = lonWidget.__owl__.component;
                if (lonComponent && lonComponent.props && lonComponent.props.record) {
                    lonComponent.props.record.update({ longitude: coordinates.longitude });
                    console.log('Longitude widget updated via OWL');
                }
            }
        } catch (error) {
            console.warn('Could not update field widgets:', error);
        }
    }
    
    triggerFormDirtyState() {
        try {
            // Try to mark the form as dirty/modified
            const formView = document.querySelector('.o_form_view');
            if (formView) {
                // Try to find and enable the save button
                const saveButton = document.querySelector('.o_form_button_save');
                if (saveButton) {
                    saveButton.disabled = false;
                    saveButton.classList.remove('disabled');
                    console.log('Save button enabled');
                }
                
                // Try to trigger form change event
                formView.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Try to access the form controller and mark it as dirty
                try {
                    const formController = this.env.services.ui.activeController;
                    if (formController && formController.model) {
                        // Mark the model as dirty
                        if (typeof formController.model.__isDirty !== 'undefined') {
                            formController.model.__isDirty = true;
                        }
                        
                        // Trigger model change notification
                        if (formController.model.notify) {
                            formController.model.notify();
                        }
                        
                        console.log('Form controller marked as dirty');
                    }
                } catch (controllerError) {
                    console.warn('Could not access form controller:', controllerError);
                }
                
                // Try to update the form state via OWL
                if (formView.__owl__ && formView.__owl__.component) {
                    const component = formView.__owl__.component;
                    if (component && component.state && component.state.isDirty !== undefined) {
                        component.state.isDirty = true;
                        console.log('OWL component state marked as dirty');
                    }
                }
            }
        } catch (error) {
            console.warn('Could not trigger form dirty state:', error);
        }
    }

    getTempCoordinates() {
        return this.tempCoordinates || null;
    }

    clearTempCoordinates() {
        this.tempCoordinates = null;
    }
}

// Register the service
registry.category('services').add('locationCapture', {
    dependencies: ['rpc', 'ui', 'notification'],
    start(env, { rpc, notification }) {
        return new LocationCaptureService(env, rpc, notification);
    },
});

// Client action for location capture
registry.category('actions').add('surepay_client_visits.capture_location', async (env, action) => {
    const locationCapture = env.services.locationCapture;
    const { model, resId } = action.params || {};
    
    try {
        await locationCapture.captureLocation(model, resId);
        env.services.notification.add(_t('Location captured successfully!'), {
            type: 'success',
        });
    } catch (error) {
        env.services.notification.add(_t('Failed to capture location.'), {
            type: 'danger',
        });
    }
    
    return { type: 'ir.actions.act_window_close' };
});
