import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    print("Importing Source...")
    from app.models.source import Source
    print("Importing Article...")
    from app.models.article import RawArticle
    print("Importing Topic...")
    from app.models.topic import Topic
    print("Importing User...")
    from app.models.user import User
    print("Importing Interaction...")
    from app.models.interaction import Comment
    print("Importing Perspective...")
    from app.models.perspective import SourceGroup
    print("Importing Impact...")
    from app.models.impact import RegionalImpact
    print("Importing Common...")
    from app.models.common import Vertical
    
    print("All imports successful!")
except Exception as e:
    print(f"Import Error: {e}")
    import traceback
    traceback.print_exc()
