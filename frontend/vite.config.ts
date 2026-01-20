import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit(),
		SvelteKitPWA({
			srcDir: 'src',
			mode: 'development',
			strategies: 'generateSW',
			registerType: 'autoUpdate',
			manifest: {
				name: 'Family Hub',
				short_name: 'FamilyHub',
				description: 'Home automation dashboard for the family',
				theme_color: '#1e3a5f',
				background_color: '#0f172a',
				display: 'standalone',
				orientation: 'portrait',
				icons: [
					{
						src: 'pwa-192x192.png',
						sizes: '192x192',
						type: 'image/png'
					},
					{
						src: 'pwa-512x512.png',
						sizes: '512x512',
						type: 'image/png'
					}
				]
			},
			workbox: {
				globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}']
			},
			devOptions: {
				enabled: true
			}
		})
	],
	server: {
		host: '0.0.0.0',
		port: 5173,
		proxy: {
			'/api': {
				target: 'http://192.168.1.95:8000',
				changeOrigin: true
			}
		}
	}
});
