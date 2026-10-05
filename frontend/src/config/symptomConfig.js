// Set verified=true only after each mapping has been verified with the model owner.
export const symptomConfig = Array.from({ length: 18 }, (_, i) => ({ modelFeature: `G${String(i + 1).padStart(2, '0')}`, label: 'Configure symptom name', description: 'Awaiting a verified model feature mapping.', verified: false }));
export const mappingsVerified = () => symptomConfig.length === 18 && symptomConfig.every(s => s.verified && s.label !== 'Configure symptom name');
export const toModelFeatures = selected => Object.fromEntries(symptomConfig.map(s => [s.modelFeature, selected.includes(s.modelFeature) ? 1 : 0]));
