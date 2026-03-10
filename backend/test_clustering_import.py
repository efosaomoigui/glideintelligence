try:
    from app.services.ai.clustering_service import ClusteringService
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Error: {e}")
