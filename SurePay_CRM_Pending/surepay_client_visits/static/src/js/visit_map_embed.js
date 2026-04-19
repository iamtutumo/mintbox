/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class VisitMapEmbedService {
    constructor(env, rpc, notification) {
        this.env = env;
        this.rpc = rpc;
        this.notification = notification;
    }

    updateMapIframe(recordId, latitude = null, longitude = null) {
        return new Promise((resolve, reject) => {
            // If coordinates are provided directly, use them
            if (latitude && longitude) {
                this.updateMapWithCoordinates(latitude, longitude)
                    .then(resolve)
                    .catch(reject);
                return;
            }
            
            // Otherwise, get coordinates from record
            if (!recordId) {
                reject(new Error('No record ID or coordinates provided'));
                return;
            }

            // Get the visit record data
            this.rpc('/web/dataset/call_kw/surepay.client.visit/read', {
                model: 'surepay.client.visit',
                method: 'read',
                args: [[recordId], ['latitude', 'longitude', 'map_iframe_url']],
                kwargs: {},
            }).then(result => {
                if (result && result.length > 0) {
                    const visit = result[0];
                    if (visit.latitude && visit.longitude && visit.map_iframe_url) {
                        // Try to find and update the iframe with retry logic
                        this.findAndUpdateIframe(visit.map_iframe_url, visit, resolve, reject);
                    } else {
                        reject(new Error('No coordinates available'));
                    }
                } else {
                    reject(new Error('Visit record not found'));
                }
            }).catch(error => {
                reject(error);
            });
        });
    }

    findAndUpdateIframe(mapUrl, visitData, resolve, reject, attempt = 1) {
        const maxAttempts = 10;
        const retryDelay = 500;

        if (attempt > maxAttempts) {
            reject(new Error('Map iframe not found after ' + maxAttempts + ' attempts'));
            return;
        }

        setTimeout(() => {
            try {
                // Try multiple selectors for the iframe
                const iframe = document.querySelector('#map_container iframe') ||
                              document.querySelector('iframe[src*="openstreetmap"]') ||
                              document.querySelector('iframe[title*="map"]');

                if (iframe) {
                    // Update iframe src
                    iframe.src = mapUrl;
                    console.log('Map iframe updated successfully');
                    
                    // Update form model with coordinates
                    this.tryUpdateFormModel(visitData.latitude, visitData.longitude);
                    
                    resolve();
                } else {
                    // Try to create iframe if missing
                    this.createIframeIfMissing(mapUrl, visitData, resolve, reject, attempt);
                }
            } catch (error) {
                console.error('Error updating map iframe:', error);
                if (attempt < maxAttempts) {
                    this.findAndUpdateIframe(mapUrl, visitData, resolve, reject, attempt + 1);
                } else {
                    reject(error);
                }
            }
        }, retryDelay);
    }

    updateMapWithCoordinates(latitude, longitude) {
        return new Promise((resolve, reject) => {
            try {
                // Create OpenStreetMap URL with marker
                const bbox = `${longitude-0.01},${latitude-0.01},${longitude+0.01},${latitude+0.01}`;
                const marker = `${latitude},${longitude}`;
                const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${marker}`;
                
                console.log('Updating map with coordinates:', latitude, longitude);
                console.log('Map URL:', mapUrl);
                
                // Try to find and update iframe with multiple selectors
                const iframe = document.querySelector('#map_container iframe') ||
                              document.querySelector('#visit_map_iframe') ||
                              document.querySelector('iframe[src*="openstreetmap"]') ||
                              document.querySelector('iframe[title*="map"]');
                
                if (iframe) {
                    // Update iframe src
                    iframe.src = mapUrl;
                    console.log('Map iframe updated successfully');
                    
                    // Update form model with coordinates
                    this.updateFormFields(latitude, longitude);
                    
                    // Ensure map container is visible
                    this.ensureMapContainerVisibility()
                        .then(() => {
                            console.log('Map update process completed successfully');
                            resolve();
                        })
                        .catch(error => {
                            console.warn('Visibility management had issues, but map update succeeded:', error);
                            resolve(); // Still resolve since map update worked
                        });
                } else {
                    // Try to find the map container even if it's invisible
                    const mapContainer = this.findMapContainer();
                    if (mapContainer) {
                        // Create iframe in the container
                        this.createIframeInContainer(mapContainer, mapUrl, { latitude, longitude }, resolve, reject);
                    } else {
                        // Container not found, try to create it
                        this.createMapContainerAndIframe(mapUrl, { latitude, longitude }, resolve, reject);
                    }
                }
            } catch (error) {
                console.error('Error updating map with coordinates:', error);
                reject(error);
            }
        });
    }

    updateFormFields(latitude, longitude) {
        try {
            // Update latitude and longitude input fields
            const latInput = document.querySelector('input[name="latitude"]');
            const lonInput = document.querySelector('input[name="longitude"]');
            
            if (latInput) {
                latInput.value = latitude;
                latInput.dispatchEvent(new Event('change', { bubbles: true }));
                latInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            if (lonInput) {
                lonInput.value = longitude;
                lonInput.dispatchEvent(new Event('change', { bubbles: true }));
                lonInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            // Update temporary coordinate fields
            const tempLatInput = document.querySelector('input[name="temp_latitude"]');
            const tempLonInput = document.querySelector('input[name="temp_longitude"]');
            
            if (tempLatInput) {
                tempLatInput.value = latitude;
            }
            
            if (tempLonInput) {
                tempLonInput.value = longitude;
            }
            
            console.log('Form fields updated with coordinates:', latitude, longitude);
        } catch (error) {
            console.warn('Could not update form fields:', error);
        }
    }

    ensureMapContainerVisibility(retryCount = 0) {
        return new Promise((resolve, reject) => {
            const maxRetries = 5;
            const retryDelay = 200;
            
            const tryEnsureVisibility = (attempt) => {
                try {
                    const mapContainer = this.findMapContainer();
                    if (mapContainer) {
                        // Make sure container and all its parents are visible
                        let element = mapContainer;
                        while (element) {
                            element.style.display = 'block';
                            element.style.visibility = 'visible';
                            element.style.opacity = '1';
                            
                            // Remove any invisible attributes
                            if (element.hasAttribute('invisible')) {
                                element.removeAttribute('invisible');
                            }
                            
                            // Remove any invisible classes
                            element.classList.remove('o_invisible_modifier', 'invisible');
                            
                            element = element.parentElement;
                        }
                        
                        // Hide the placeholder div
                        const placeholder = mapContainer.parentElement?.querySelector('div[invisible*="latitude or longitude"]');
                        if (placeholder) {
                            placeholder.style.display = 'none';
                            placeholder.style.visibility = 'hidden';
                        }
                        
                        // Also try to hide any other placeholder divs
                        const placeholders = mapContainer.parentElement?.querySelectorAll('div');
                        if (placeholders) {
                            placeholders.forEach(div => {
                                if (div.textContent.includes('Click') && div.textContent.includes('Capture Current Location')) {
                                    div.style.display = 'none';
                                    div.style.visibility = 'hidden';
                                }
                            });
                        }
                        
                        console.log('Map container visibility ensured');
                        resolve();
                    } else {
                        if (attempt < maxRetries) {
                            setTimeout(() => tryEnsureVisibility(attempt + 1), retryDelay);
                        } else {
                            console.warn('Map container not found for visibility management after', maxRetries, 'attempts');
                            resolve(); // Don't reject, just resolve to continue flow
                        }
                    }
                } catch (error) {
                    if (attempt < maxRetries) {
                        setTimeout(() => tryEnsureVisibility(attempt + 1), retryDelay);
                    } else {
                        console.warn('Could not ensure map container visibility after', maxRetries, 'attempts:', error);
                        resolve(); // Don't reject, just resolve to continue flow
                    }
                }
            };
            
            tryEnsureVisibility(0);
        });
    }

    findMapContainer() {
        try {
            // Try to find the map container with various selectors
            let container = document.getElementById('map_container');
            
            if (!container) {
                // Try to find it by looking for the parent div that contains the location tab content
                const locationPages = document.querySelectorAll('.notebook-page, .tab-content, .o_form_sheet_bg');
                for (let page of locationPages) {
                    if (page?.textContent?.includes('Location') || page?.querySelector('[name*="location"]')) {
                        container = page.querySelector('[id*="map"]') || page.querySelector('[style*="height: 400px"]') || page.querySelector('[style*="height:400px"]');
                        if (container) break;
                    }
                }
            }
            
            if (!container) {
                // Try to find any div that might be the map container
                const allDivs = document.querySelectorAll('div');
                for (let div of allDivs) {
                    if (div?.style && (div.style.height === '400px' || div.style.height?.includes('400px'))) {
                        const parent = div.parentElement;
                        if (parent?.textContent?.includes('Location')) {
                            container = div;
                            break;
                        }
                    }
                }
            }
            
            // Final fallback: look for any iframe with openstreetmap and get its parent
            if (!container) {
                const mapIframe = document.querySelector('iframe[src*="openstreetmap"]');
                if (mapIframe) {
                    container = mapIframe.parentElement;
                }
            }
            
            return container;
        } catch (error) {
            console.warn('Error in findMapContainer:', error);
            return null;
        }
    }

    createIframeInContainer(mapContainer, mapUrl, visitData, resolve, reject) {
        try {
            // Clear existing content
            mapContainer.innerHTML = '';
            
            // Create new iframe
            const iframe = document.createElement('iframe');
            iframe.src = mapUrl;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.title = 'Visit Location Map';
            iframe.id = 'visit_map_iframe';
            iframe.setAttribute('allowfullscreen', '');
            iframe.setAttribute('frameborder', '0');
            
            mapContainer.appendChild(iframe);
            
            // Ensure container is visible
            this.ensureMapContainerVisibility()
                .then(() => {
                    console.log('Map iframe created in container successfully');
                    
                    // Update form fields
                    this.updateFormFields(visitData.latitude, visitData.longitude);
                    
                    resolve();
                })
                .catch(error => {
                    console.warn('Visibility management had issues, but iframe creation succeeded:', error);
                    // Still resolve since iframe creation worked
                    this.updateFormFields(visitData.latitude, visitData.longitude);
                    resolve();
                });
        } catch (error) {
            console.error('Error creating iframe in container:', error);
            reject(error);
        }
    }

    createMapContainerAndIframe(mapUrl, visitData, resolve, reject) {
        try {
            // Find the location tab or page
            const locationTab = this.findLocationTab();
            if (!locationTab) {
                reject(new Error('Location tab not found'));
                return;
            }
            
            // Create map container
            const mapContainer = document.createElement('div');
            mapContainer.id = 'map_container';
            mapContainer.style.width = '100%';
            mapContainer.style.height = '400px';
            mapContainer.style.border = '1px solid #ccc';
            mapContainer.style.overflow = 'hidden';
            
            // Create iframe
            const iframe = document.createElement('iframe');
            iframe.src = mapUrl;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.title = 'Visit Location Map';
            iframe.id = 'visit_map_iframe';
            iframe.setAttribute('allowfullscreen', '');
            iframe.setAttribute('frameborder', '0');
            
            mapContainer.appendChild(iframe);
            
            // Insert the container into the location tab
            locationTab.appendChild(mapContainer);
            
            // Ensure container is visible
            this.ensureMapContainerVisibility()
                .then(() => {
                    console.log('Map container and iframe created successfully');
                    
                    // Update form fields
                    this.updateFormFields(visitData.latitude, visitData.longitude);
                    
                    resolve();
                })
                .catch(error => {
                    console.warn('Visibility management had issues, but container and iframe creation succeeded:', error);
                    // Still resolve since container and iframe creation worked
                    this.updateFormFields(visitData.latitude, visitData.longitude);
                    resolve();
                });
        } catch (error) {
            console.error('Error creating map container and iframe:', error);
            reject(error);
        }
    }

    findLocationTab() {
        try {
            // Try to find the location tab by various methods
            let locationTab = null;
            
            // Look for tab with 'Location' text
            const tabs = document.querySelectorAll('.notebook-page, .tab-content, .o_form_sheet_bg, .o_form_view');
            for (let tab of tabs) {
                if (tab?.textContent?.includes('Location')) {
                    locationTab = tab;
                    break;
                }
            }
            
            // If not found, try to find by coordinate fields
            if (!locationTab) {
                const latField = document.querySelector('input[name="latitude"]');
                if (latField) {
                    locationTab = latField.closest('.notebook-page, .tab-content, .o_form_sheet_bg, .sheet, .o_form_view');
                }
            }
            
            // If still not found, try to find by longitude fields
            if (!locationTab) {
                const lonField = document.querySelector('input[name="longitude"]');
                if (lonField) {
                    locationTab = lonField.closest('.notebook-page, .tab-content, .o_form_sheet_bg, .sheet, .o_form_view');
                }
            }
            
            // Final fallback: look for any element containing location-related text
            if (!locationTab) {
                const allElements = document.querySelectorAll('*');
                for (let element of allElements) {
                    if (element?.textContent?.includes('Location') && (element.classList.contains('notebook-page') || element.classList.contains('tab-content') || element.classList.contains('o_form_sheet_bg'))) {
                        locationTab = element;
                        break;
                    }
                }
            }
            
            return locationTab;
        } catch (error) {
            console.warn('Error in findLocationTab:', error);
            return null;
        }
    }

    forceMapContainerVisibility() {
        try {
            const mapContainer = document.getElementById('map_container');
            if (mapContainer) {
                // Make sure container and its parents are visible
                let element = mapContainer;
                while (element) {
                    element.style.display = 'block';
                    element.style.visibility = 'visible';
                    element = element.parentElement;
                }
            }
        } catch (error) {
            console.warn('Could not force map container visibility:', error);
        }
    }

    initializeMapForForm() {
        // Wait for the form to be fully loaded with multiple attempts
        const tryInitializeMap = (attempt = 1) => {
            setTimeout(() => {
                try {
                    const mapContainer = document.getElementById('map_container');
                    if (mapContainer) {
                        // Check if we have coordinates in the form
                        const latInput = document.querySelector('input[name="latitude"]');
                        const lonInput = document.querySelector('input[name="longitude"]');
                        
                        if (latInput && lonInput && latInput.value && lonInput.value) {
                            const latitude = parseFloat(latInput.value);
                            const longitude = parseFloat(lonInput.value);
                            
                            if (!isNaN(latitude) && !isNaN(longitude)) {
                                this.updateMapWithCoordinates(latitude, longitude)
                                    .catch(error => {
                                        console.warn('Could not initialize map with form coordinates:', error);
                                    });
                            }
                        }
                    } else if (attempt < 10) {
                        tryInitializeMap(attempt + 1);
                    }
                } catch (error) {
                    console.warn('Error during map initialization:', error);
                    if (attempt < 10) {
                        tryInitializeMap(attempt + 1);
                    }
                }
            }, 1000 * attempt); // Increasing delay
        };

        tryInitializeMap();
    }
}

// Register the service
registry.category('services').add('visitMapEmbed', {
    dependencies: ['rpc', 'notification'],
    start(env, { rpc, notification }) {
        return new VisitMapEmbedService(env, rpc, notification);
    },
});

// Client action to update map when coordinates change
export const UpdateMapAction = {
    async start(env, { rpc, notification }) {
        const visitMapEmbed = new VisitMapEmbedService(env, rpc, notification);
        return { type: 'ir.actions.act_window_close' };
    },
};

registry.category('actions').add('visit_map_embed.update', UpdateMapAction);
