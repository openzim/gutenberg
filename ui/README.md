# Gutenberg UI

Vue.js 3 frontend for Project Gutenberg ZIM files.

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Modern build tool
- **Vue Router** - Client-side routing (hash mode for ZIM compatibility)
- **Pinia** - State management
- **Vuetify 3** - Material Design component framework
- **@vitejs/plugin-legacy** - Browser compatibility for older browsers

## Development

### Prerequisites

- Node.js 20+ (or use Yarn)
- npm or yarn

### Install Dependencies

```bash
npm install
# or
yarn install
```

### Development Server

```bash
npm run dev
# or
yarn dev
```

The app will be available at `http://localhost:5173`

### Build

```bash
npm run build
# or
yarn build
```

The built files will be in the `dist/` directory, which will be packaged into the ZIM file by the Python scraper.

### Type Checking

```bash
npm run type-check
# or
yarn type-check
```

### Linting

```bash
npm run lint
# or
yarn lint
```

### Formatting

```bash
npm run format
# or
yarn format
```

## Project Structure

```
ui/
├── src/
│   ├── assets/          # CSS, images, fonts
│   ├── components/       # Vue components
│   │   └── common/       # Shared components
│   ├── plugins/          # Vue plugins (Vuetify, etc.)
│   ├── router/          # Vue Router configuration
│   ├── stores/           # Pinia stores
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── views/            # Page components
│   ├── App.vue           # Root component
│   └── main.ts           # Application entry point
├── public/               # Static assets
├── index.html            # HTML template
├── package.json          # Dependencies and scripts
├── vite.config.ts        # Vite configuration
└── tsconfig.json         # TypeScript configuration
```

## Browser Compatibility

The UI is built to work with:
- Modern browsers (ES6+)
- Older browsers via `@vitejs/plugin-legacy` (polyfills and transpilation)
- Kiwix readers (kiwix-serve, kiwix-js, kiwix-apple, kiwix-android)

## No-JS Fallback

A basic HTML fallback will be provided for users with JavaScript disabled (Issue #345).

