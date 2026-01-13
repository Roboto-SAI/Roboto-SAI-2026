/**
 * Roboto SAI Environment Configuration
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 * 
 * Configure these values for your production environment
 */

export const config = {
  // API Configuration - Connect to your Python backend
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  
  // Grok/xAI API Configuration
  grokApiUrl: import.meta.env.VITE_GROK_API_URL || 'https://api.x.ai/v1',
  
  // Application Settings
  appName: 'Roboto SAI',
  appVersion: '1.0.0',
  
  // Theme Settings
  defaultTheme: 'Regio-Aztec Fire #42',
  
  // Creator Credits
  creator: 'Roberto Villarreal Martinez',
  copyright: '© 2025 Roberto Villarreal Martinez',
  
  // Cultural Genome Settings
  genomeVersion: 'v2.2',
  genomeFile: 'roboto_culture_legacy_v2.2.py',
};
