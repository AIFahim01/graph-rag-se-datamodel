# Frontend Image Display Fix

## The Issue
Images are being served by the API but not displayed in frontend.

## API Provides
Each search result includes:
```json
{
  "image_url": "/images/GC_2021/.../page-13.png",
  "metadata": {
    "customer": "HVDC Customer",
    "technology": "HVDC",
    "year": 2022,
    ...
  }
}
```

## To Display Images in Frontend

### 1. Update the result display component:
In your React/Next.js component that displays search results, add:

```jsx
{result.image_url && (
  <img
    src={`http://localhost:8001${result.image_url}`}
    alt={`Page ${result.metadata.page}`}
    style={{ maxWidth: '100%', height: 'auto' }}
  />
)}
```

### 2. Or configure Next.js image domains:
In `next.config.mjs`, add:

```javascript
module.exports = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8001',
        pathname: '/images/**',
      },
    ],
  },
}
```

### 3. Test Image URLs
You can directly access images in browser:
```
http://localhost:8001/images/GC_2021/GC21_009%20NEOM%20Grid%20Consultation/4%20Deliverables/Annexes/Annex_7_220421_NeomGridDesign_Interim_HVDC/pages/Annex_7_220421_NeomGridDesign_Interim_HVDC%20-%20page%2013.png
```

## Available Metadata Fields
All these are included in search results:
- `customer` - Company/customer name
- `project` - Project ID
- `project_name` - Full project name
- `technology` - HVDC/SynCon/Other
- `year` - Document year
- `page` - Page number
- `file_name` - Original PDF name
- `total_images` - Image count in document
- `total_tables` - Table count

## Testing the API
```bash
# Search with metadata filters
curl "http://localhost:8001/api/search?q=HVDC&technology=HVDC&year=2022&top_k=5"

# Get all HVDC projects
curl "http://localhost:8001/api/projects?technology=HVDC"

# Get statistics
curl "http://localhost:8001/api/stats"
```