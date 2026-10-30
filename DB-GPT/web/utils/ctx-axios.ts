import axios from 'axios';
import { localizeUiMetadata } from '@/lib/ui-zh';

const api = axios.create({
  baseURL: process.env.API_BASE_URL ?? '',
});

api.defaults.timeout = 10000;

api.interceptors.response.use(
  response => localizeUiMetadata(response.data),
  err => Promise.reject(err),
);

export default api;
