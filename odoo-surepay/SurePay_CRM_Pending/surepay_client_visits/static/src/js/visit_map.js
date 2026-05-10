/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class VisitMapService {
    constructor(env, rpc, notification) {
        this.env = env;
        this.rpc = rpc;
        this.notification = notification;
    }

    initializeMap(mapElementId, options = {}) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                try {
                    const mapElement = document.getElementById(mapElementId);
                    if (!mapElement) {
                        reject(new Error(`Map element with ID '${mapElementId}' not found`));
                        return;
                    }

                    // Create iframe for OpenStreetMap
                    const iframe = document.createElement('iframe');
                    iframe.style.width = '100%';
                    iframe.style.height = '100%';
                    iframe.style.border = 'none';
                    iframe.style.borderRadius = '4px';
                    
                    // Default center coordinates (can be overridden by options)
                    const centerLat = options.centerLat || 0;
                    const centerLon = options.centerLon || 0;
                    const zoom = options.zoom || 13;
                    
                    // Create OpenStreetMap embed URL
                    const bbox = `${centerLon-0.01},${centerLat-0.01},${centerLon+0.01},${centerLat+0.01}`;
                    const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik`;
                    
                    iframe.src = mapUrl;
                    iframe.title = 'Client Visits Map';
                    
                    // Clear existing content and add iframe
                    mapElement.innerHTML = '';
                    mapElement.appendChild(iframe);
                    
                    console.log('Map initialized successfully');
                    resolve(iframe);
                } catch (error) {
                    console.error('Error initializing map:', error);
                    reject(error);
                }
            }, 500); // Small delay to ensure DOM is ready
        });
    }

    updateMapWithVisits(mapElementId, visits) {
        return new Promise((resolve, reject) => {
            try {
                if (!visits || visits.length === 0) {
                    console.log('No visits to display on map');
                    resolve();
                    return;
                }

                // Calculate center point from all visits
                let totalLat = 0, totalLon = 0, validVisits = 0;
                
                visits.forEach(visit => {
                    if (visit.latitude && visit.longitude) {
                        totalLat += parseFloat(visit.latitude);
                        totalLon += parseFloat(visit.longitude);
                        validVisits++;
                    }
                });

                if (validVisits === 0) {
                    console.log('No valid coordinates found in visits');
                    resolve();
                    return;
                }

                const centerLat = totalLat / validVisits;
                const centerLon = totalLon / validVisits;

                // Initialize map centered on the average position
                this.initializeMap(mapElementId, {
                    centerLat: centerLat,
                    centerLon: centerLon,
                    zoom: 10
                }).then(() => {
                    console.log(`Map updated with ${validVisits} visits`);
                    resolve();
                }).catch(reject);

            } catch (error) {
                console.error('Error updating map with visits:', error);
                reject(error);
            }
        });
    }

    loadVisitsForMap(domain = []) {
        return new Promise((resolve, reject) => {
            this.rpc('/web/dataset/call_kw/surepay.client.visit/read_group', {
                model: 'surepay.client.visit',
                method: 'read_group',
                args: [],
                kwargs: {
                    domain: domain,
                    fields: ['latitude', 'longitude', 'partner_id', 'visit_date', 'user_id'],
                    groupby: [],
                    lazy: false,
                },
            }).then(result => {
                // Transform read_group result to visit records
                const visits = result.map(group => ({
                    id: group.id,
                    latitude: group.latitude,
                    longitude: group.longitude,
                    partner_id: group.partner_id,
                    visit_date: group.visit_date,
                    user_id: group.user_id,
                })).filter(visit => visit.latitude && visit.longitude);

                resolve(visits);
            }).catch(error => {
                console.error('Error loading visits for map:', error);
                reject(error);
            });
        });
    }

    refreshMap(mapElementId, domain = []) {
        return new Promise((resolve, reject) => {
            this.loadVisitsForMap(domain)
                .then(visits => {
                    return this.updateMapWithVisits(mapElementId, visits);
                })
                .then(resolve)
                .catch(reject);
        });
    }
}

// Register the service
registry.category('services').add('visitMap', {
    dependencies: ['rpc', 'notification'],
    start(env, { rpc, notification }) {
        return new VisitMapService(env, rpc, notification);
    },
});

// Client action for visit map
export const VisitMapClientAction = {
    async start(env, { rpc, notification }) {
        const visitMap = new VisitMapService(env, rpc, notification);
        
        // Initialize the map when the action is opened
        try {
            await visitMap.refreshMap('all_visits_map');
            env.services.notification.add(_t('Map loaded successfully!'), {
                type: 'success',
            });
        } catch (error) {
            console.error('Failed to load map:', error);
            env.services.notification.add(_t('Failed to load map. Please try again.'), {
                type: 'danger',
            });
        }
        
        return { type: 'ir.actions.act_window_close' };
    },
};

registry.category('actions').add('visit_map.load', VisitMapClientAction);
