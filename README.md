# Universal Web Image Downloader

A smart, configurable, and automated tool designed specifically to **find and download high-resolution product images** from any e-commerce website.

Unlike generic scrapers, this tool is optimized for visual content—it intelligently detects product pages, filters out low-quality icons, and saves organized image galleries for each product.

## Key Features

- **📸 Image-First Approach**: Automatically finds the highest resolution version of product images.
- **🧠 Auto-Discovery**: Uses smart heuristics to identify product pages and images without needing any configuration.
- **🎯 Precision Precision**: Can be customized with CSS selectors to download exactly what you want (e.g., only main gallery images).
- **📂 Organized Output**: Saves images in folders named after the product, keeping your downloads clean and sorted.
- **🚀 Smart Traversing**: Crawls the site efficiently to build your image library.
- **resume**: Skips files that have already been downloaded to save time and bandwidth.

## Installation

1. Clone or download this repository.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### 🚀 Quick Start (Auto-Discovery)
Just provide the website URL. The tool will scan the site, detect products, and start downloading images automatically.

```bash
python scraper.py https://example.com/shop
```

### 🛠️ Advanced Usage (Custom Selectors)
For the best results on complex sites, tell the tool exactly where to look using CSS selectors.

```bash
python scraper.py https://example.com/shop \
  --product-selector ".product-detail-page" \
  --image-selector ".gallery-image img" \
  --name-selector "h1.product-title"
```

### Configuration Options

| Argument | Description | Default |
|----------|-------------|---------|
| `url` | Target website URL to start scanning. | Required |
| `--folder` | Output directory for downloaded images. | `downloads` |
| `--max` | Maximum number of pages to scan. | `100` |
| `--delay` | Delay in seconds between requests. | `0.5` |
| `--product-selector` | CSS selector to identify a product page. | Auto-detect |
| `--image-selector` | CSS selector to find product images. | Auto-detect |
| `--name-selector` | CSS selector to find the product name. | Auto-detect |

## Example Scenarios

**Scenario 1: Downloading from a Shopify store**
```bash
python scraper.py https://cool-shop.com/collections/all
```

**Scenario 2: Downloading only main product photos from a specific site**
```bash
python scraper.py https://myshop.com \
  --image-selector ".main-product-photo img"
```

## License

This project is open source and available under the [MIT License](LICENSE).
