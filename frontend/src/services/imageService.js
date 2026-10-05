import {api} from './api.js';

export function validateImage(file) {
  if (!file || file.size === 0) throw new Error('Choose a non-empty cattle image.');
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) throw new Error('Choose a JPEG, PNG or WebP image.');
  if (file.size > 10 * 1024 * 1024) throw new Error('Image exceeds the 10 MiB upload limit.');
}

export async function predictImage(file) {
  validateImage(file);
  const form = new FormData();
  form.append('file', file);
  const response = await api.post('/predict/image', form, {
    headers: {'Content-Type': undefined}, timeout: 60000,
  });
  return response.data;
}
