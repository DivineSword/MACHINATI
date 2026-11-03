import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendRoot = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
	plugins: [react()],
	server: { proxy: { '/api': 'http://127.0.0.1:8000', '/health': 'http://127.0.0.1:8000' } },
	build: {
		rollupOptions: {
			input: {
				app: resolve(frontendRoot, 'index.html'),
				cooperative: resolve(frontendRoot, 'cooperative.html'),
				operations: resolve(frontendRoot, 'equipe-machinati.html'),
			},
		},
	},
});
