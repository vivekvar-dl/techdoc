import nltk
import os
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NLTKDownloader:
    """Handles downloading and verification of NLTK data packages"""
    
    REQUIRED_PACKAGES = [
        'punkt',
        'averaged_perceptron_tagger',
        'words',
        'maxent_ne_chunker',
        'stopwords',
        'wordnet',
        'omw-1.4'
    ]

    @staticmethod
    def download_nltk_data() -> Dict[str, bool]:
        """
        Downloads all required NLTK data packages.
        Returns a dictionary with package names and their download status.
        """
        download_status = {}
        
        logger.info("Starting NLTK data download...")
        
        # Create NLTK data directory if it doesn't exist
        nltk_data_dir = os.path.expanduser('~/nltk_data')
        if not os.path.exists(nltk_data_dir):
            os.makedirs(nltk_data_dir)
            logger.info(f"Created NLTK data directory at {nltk_data_dir}")

        # Download each required package
        for package in NLTKDownloader.REQUIRED_PACKAGES:
            try:
                logger.info(f"Downloading {package}...")
                nltk.download(package, quiet=True)
                download_status[package] = True
                logger.info(f"Successfully downloaded {package}")
            except Exception as e:
                download_status[package] = False
                logger.error(f"Failed to download {package}: {str(e)}")
        
        return download_status

    @staticmethod
    def verify_nltk_data() -> Dict[str, bool]:
        """
        Verifies that all required NLTK data packages are installed.
        Returns a dictionary with package names and their verification status.
        """
        verification_status = {}
        package_paths = {
            'punkt': 'tokenizers/punkt',
            'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger',
            'words': 'corpora/words',
            'maxent_ne_chunker': 'chunkers/maxent_ne_chunker',
            'stopwords': 'corpora/stopwords',
            'wordnet': 'corpora/wordnet.zip',
            'omw-1.4': 'corpora/omw-1.4.zip'
        }
        
        logger.info("Verifying NLTK data packages...")
        
        for package, path in package_paths.items():
            try:
                # Special handling for zip files
                if path.endswith('.zip'):
                    is_installed = os.path.exists(os.path.join(os.path.expanduser('~/nltk_data'), path))
                else:
                    is_installed = nltk.data.find(path) is not None
                verification_status[package] = is_installed
                status_msg = "installed" if is_installed else "not installed"
                logger.info(f"Package {package} is {status_msg}")
            except LookupError:
                verification_status[package] = False
                logger.warning(f"Package {package} is not installed")
        
        return verification_status

def main():
    """Main function to download and verify NLTK data"""
    logger.info("Starting NLTK data download and verification process...")
    
    # Download NLTK data
    download_status = NLTKDownloader.download_nltk_data()
    
    # Verify installation
    verification_status = NLTKDownloader.verify_nltk_data()
    
    # Report results
    logger.info("\nDownload Results:")
    for package, status in download_status.items():
        logger.info(f"{package}: {'Success' if status else 'Failed'}")
    
    logger.info("\nVerification Results:")
    for package, status in verification_status.items():
        logger.info(f"{package}: {'Installed' if status else 'Not Installed'}")
    
    # Check if any packages failed
    failed_packages = [pkg for pkg, status in verification_status.items() if not status]
    if failed_packages:
        logger.error(f"\nThe following packages are not properly installed: {', '.join(failed_packages)}")
        logger.error("Please try downloading these packages manually or check your internet connection.")
    else:
        logger.info("\nAll required NLTK packages are successfully installed!")

if __name__ == "__main__":
    main() 