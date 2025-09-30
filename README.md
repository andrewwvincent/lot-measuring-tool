# 🗺️ Lot Measuring Tool

A web-based Google Maps application for measuring and analyzing school campus areas with precision and ease.

## 🌟 Features

- **🗺️ Interactive Google Maps** with satellite and hybrid views
- **📐 Precise area measurement** using lat/lng coordinates
- **🏢 Building analysis** with Street View integration for floor counting
- **📊 Real-time calculations** in acres and square feet
- **🎯 Multiple area types**: boundaries, buildings, fields, parking lots
- **📱 Mobile-friendly** responsive design
- **📋 Export functionality** to CSV for reporting

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Maps API key with the following APIs enabled:
  - Maps JavaScript API
  - Geocoding API
  - Static Maps API
  - Street View Static API

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/andrewwvincent/lot-measuring-tool.git
   cd lot-measuring-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google Maps API key
   ```

4. **Run the application**
   ```bash
   python maps_analyzer_app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5001
   ```

## 📖 How to Use

### Basic Workflow
1. **Search for an address** or select from the provided Austin school list
2. **Switch between views**:
   - **Satellite**: Best for accurate area measurement
   - **Hybrid**: Shows building labels and 3D perspective
3. **Select drawing tools** from the sidebar
4. **Draw polygons** by clicking points around areas
5. **Double-click** to finish each shape
6. **For buildings**: Click finished polygons to open Street View and set floor count
7. **View real-time statistics** in the sidebar
8. **Export results** when complete

### Drawing Tools
- **🏫 School Boundary** - Overall property boundary
- **🏢 Buildings** - Structures (click to set floors)
- **🏃 Playing Fields** - Sports fields and courts
- **🚗 Parking** - Parking lots and areas
- **🌳 Outdoor Space** - Other outdoor areas

### Street View Integration
- **Click any building polygon** to open Street View
- **Visually count floors** using window rows and building height
- **Set floor count** to calculate total building square footage
- **Navigate around** the building for better views

## 🛠️ Technical Details

### Architecture
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Maps**: Google Maps API with Drawing Library
- **Calculations**: Shapely for geometric operations, PyProj for coordinate transformations

### Key Features
- **Accurate measurements** using UTM projection for area calculations
- **Real-time editing** with draggable polygon points
- **Persistent data** storage during session
- **Error handling** and user feedback
- **Responsive design** for desktop and mobile

### File Structure
```
lot-measuring-tool/
├── maps_analyzer_app.py      # Main Flask application
├── templates/
│   └── maps_index.html       # Web interface
├── addresses.csv             # Sample school addresses
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

## 📊 Sample Data

Includes 35+ Austin-area school addresses for testing:
- Elementary schools
- Middle schools  
- High schools
- Charter schools

## 🔧 Configuration

### Environment Variables
```bash
GOOGLE_MAPS_API_KEY=your_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

### Google Maps API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable required APIs
4. Create credentials (API key)
5. Restrict key to your domain (recommended)

## 📱 Mobile Support

The application is fully responsive and works on mobile devices:
- Touch-friendly drawing interface
- Optimized for tablet use
- Mobile-friendly file exports

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Google Maps Platform for mapping services
- Austin ISD for inspiration and testing data
- Texas school districts for real-world use cases

---

**Perfect for school facility planning, real estate analysis, and educational research** 🎓
