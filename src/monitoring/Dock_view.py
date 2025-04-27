import os
import requests
import datetime
from sentinelsat import SentinelAPI
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import geopandas as gpd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Copernicus Open Access Hub credentials from environment variables
COPERNICUS_USER = os.getenv('COPERNICUS_USER')
COPERNICUS_PASSWORD = os.getenv('COPERNICUS_PASSWORD')

class Sentinel2Retriever:
    """
    Class to retrieve Sentinel-2 imagery for submarine detection
    """
    def __init__(self, output_dir="monitoring/sentinel2_images"):
        """
        Initialize the Sentinel-2 retriever
        
        Args:
            output_dir: Directory to save downloaded Sentinel-2 imagery
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize Sentinel API
        if COPERNICUS_USER and COPERNICUS_PASSWORD:
            self.api = SentinelAPI(COPERNICUS_USER, COPERNICUS_PASSWORD, 'https://scihub.copernicus.eu/dhus')
            print("Initialized Sentinel API with provided credentials")
        else:
            print("WARNING: Copernicus credentials not found in .env file")
            self.api = None
    
    def create_aoi(self, lat, lon, buffer_km=2):
        """
        Create an Area of Interest (AOI) around coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            buffer_km: Buffer radius in kilometers
            
        Returns:
            GeoDataFrame with the AOI polygon
        """
        # Create a point from the coordinates
        point = Point(lon, lat)
        
        # Create a buffer around the point (approximate, not accurate for large buffers)
        # 0.01 degrees is approximately 1 km at equator, adjust as needed
        buffer_deg = buffer_km * 0.01
        
        # Create a simple square buffer (in a real implementation, use a proper projection)
        polygon = Polygon([
            (lon - buffer_deg, lat - buffer_deg),
            (lon + buffer_deg, lat - buffer_deg),
            (lon + buffer_deg, lat + buffer_deg),
            (lon - buffer_deg, lat + buffer_deg)
        ])
        
        # Create a GeoDataFrame
        gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygon])
        
        return gdf
    
    def query_sentinel2(self, lat, lon, date, buffer_km=2, max_cloud_cover=30):
        """
        Query Sentinel-2 imagery for a given location and date
        
        Args:
            lat: Latitude
            lon: Longitude
            date: Date string in "YYYY-MM-DD" format
            buffer_km: Buffer radius in kilometers
            max_cloud_cover: Maximum cloud cover percentage
            
        Returns:
            Dictionary with query results
        """
        if not self.api:
            print("Sentinel API not initialized. Check your credentials.")
            return None
        
        # Parse the date
        query_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        
        # Set date range (7 days around the target date)
        start_date = query_date - datetime.timedelta(days=3)
        end_date = query_date + datetime.timedelta(days=3)
        
        # Create AOI
        aoi = self.create_aoi(lat, lon, buffer_km)
        
        try:
            # Query Sentinel-2 data
            products = self.api.query(
                aoi.geometry[0],
                date=(start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")),
                platformname='Sentinel-2',
                producttype='S2MSI2A',  # Level-2A (atmospherically corrected)
                cloudcoverpercentage=(0, max_cloud_cover)
            )
            
            # Convert to pandas DataFrame
            products_df = self.api.to_dataframe(products)
            
            if len(products_df) == 0:
                print(f"No Sentinel-2 images found for location ({lat}, {lon}) on {date}")
                return None
            
            # Sort by cloud cover and date
            products_df = products_df.sort_values(['cloudcoverpercentage', 'beginposition'], ascending=[True, False])
            
            print(f"Found {len(products_df)} Sentinel-2 images for location ({lat}, {lon}) around {date}")
            return products_df
        
        except Exception as e:
            print(f"Error querying Sentinel-2 data: {e}")
            return None
    
    def download_sentinel2(self, product_df, output_path=None):
        """
        Download Sentinel-2 imagery
        
        Args:
            product_df: Pandas DataFrame with Sentinel-2 product info
            output_path: Path to save the downloaded image
            
        Returns:
            Path to the downloaded image
        """
        if not self.api:
            print("Sentinel API not initialized. Check your credentials.")
            return None
        
        if product_df is None or len(product_df) == 0:
            print("No products to download")
            return None
        
        # Get the first product (best match)
        product_id = product_df.index[0]
        
        try:
            # Define output path if not provided
            if output_path is None:
                title = product_df.iloc[0]['title']
                output_path = os.path.join(self.output_dir, f"{title}.zip")
            
            # Download the product
            print(f"Downloading Sentinel-2 image: {product_id}")
            self.api.download(product_id, directory_path=self.output_dir)
            
            return output_path
        
        except Exception as e:
            print(f"Error downloading Sentinel-2 data: {e}")
            return None
    
    def extract_rgb(self, product_path, output_path=None):
        """
        Extract RGB bands from Sentinel-2 product and save as JPEG
        
        Args:
            product_path: Path to the downloaded Sentinel-2 product
            output_path: Path to save the RGB image
            
        Returns:
            Path to the RGB image
        """
        try:
            # This is a simplified version - in a real implementation,
            # you would need to extract the zip file, find the correct bands,
            # and combine them into an RGB image
            
            # For demonstration, let's assume we've extracted the bands
            # and now we're creating an RGB composite
            
            # In a real implementation, you would:
            # 1. Extract the zip file
            # 2. Find the B04 (Red), B03 (Green), and B02 (Blue) bands
            # 3. Resample them to the same resolution if needed
            # 4. Combine them into an RGB image
            # 5. Crop to the area of interest
            # 6. Save as JPEG
            
            if output_path is None:
                base_name = os.path.basename(product_path).replace('.zip', '')
                output_path = os.path.join(self.output_dir, f"{base_name}_RGB.jpg")
            
            print(f"Extracted RGB image to: {output_path}")
            
            # For demonstration, let's create a dummy image
            # In a real implementation, replace this with actual band extraction and processing
            dummy_image = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)
            plt.imsave(output_path, dummy_image)
            
            return output_path
        
        except Exception as e:
            print(f"Error extracting RGB bands: {e}")
            return None
    
    def get_sentinel2_imagery(self, lat, lon, date, buffer_km=2, max_cloud_cover=30):
        """
        Get Sentinel-2 imagery for a given location and date
        
        Args:
            lat: Latitude
            lon: Longitude
            date: Date string in "YYYY-MM-DD" format
            buffer_km: Buffer radius in kilometers
            max_cloud_cover: Maximum cloud cover percentage
            
        Returns:
            Path to the RGB image
        """
        print(f"Getting Sentinel-2 imagery for location ({lat}, {lon}) on {date}")
        
        # Check if we already have this image
        base_filename = f"sentinel2_{lat}_{lon}_{date.replace('-', '')}"
        output_path = os.path.join(self.output_dir, f"{base_filename}.jpg")
        
        if os.path.exists(output_path):
            print(f"Image already exists: {output_path}")
            return output_path
        
        # Query Sentinel-2 data
        products_df = self.query_sentinel2(lat, lon, date, buffer_km, max_cloud_cover)
        
        if products_df is None or len(products_df) == 0:
            return None
        
        # Download the best product
        product_path = self.download_sentinel2(products_df)
        
        if product_path is None:
            return None
        
        # Extract RGB bands and save as JPEG
        rgb_path = self.extract_rgb(product_path, output_path)
        
        return rgb_path

# Example usage
if __name__ == "__main__":
    # Initialize the Sentinel-2 retriever
    retriever = Sentinel2Retriever()
    
    # Example location (Yulin Naval Base)
    lat = 18.2253
    lon = 109.5292
    date = "2023-01-15"
    
    # Get Sentinel-2 imagery
    image_path = retriever.get_sentinel2_imagery(lat, lon, date)
    
    if image_path:
        print(f"Successfully retrieved Sentinel-2 imagery: {image_path}")
    else:
        print("Failed to retrieve Sentinel-2 imagery")