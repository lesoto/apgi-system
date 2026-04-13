"""
Genetic Data Connector for APGI System
=======================================

Connects to PGC (Psychiatric Genomics Consortium) GWAS datasets via Hugging Face.
Supports Major Depressive Disorder (MDD) and Anxiety disorder GWAS summary statistics.
"""

import logging

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    import pandas as pd
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    logger.warning("pandas or datasets not available. Install with: pip install pandas datasets")


class PGCDataConnector:
    """
    Connects to Hugging Face datasets for PGC Major Depressive Disorder (MDD) 
    and Anxiety GWAS summary statistics.
    """
    
    DATASETS = {
        "MDD": "introvoyz041/pgc-mdd",
        "Anxiety": "introvoyz041/pgc-anxiety"
    }

    def __init__(self, dataset_key="MDD"):
        self.repo_id = self.DATASETS.get(dataset_key, self.DATASETS["MDD"])
        self.df = None

    def fetch_data(self, split="train", streaming=True):
        """
        Loads the dataset from Hugging Face.
        Using streaming=True is recommended for genetic data due to large file sizes.
        
        Args:
            split: Dataset split to load (default: "train")
            streaming: Whether to use streaming mode (default: True)
            
        Returns:
            pd.DataFrame: Genetic variants data or None if failed
        """
        if not DATASETS_AVAILABLE:
            logger.error("datasets library not available. Install with: pip install datasets")
            return None
            
        try:
            logger.info(f"Connecting to Hugging Face: {self.repo_id}...")
            # Load dataset
            dataset = load_dataset(self.repo_id, split=split, streaming=streaming)
            
            # If streaming, we take the first 10,000 rows for analysis/GUI preview
            if streaming:
                iterable = iter(dataset)
                rows = [next(iterable) for _ in range(10000)]
                self.df = pd.DataFrame(rows)
            else:
                self.df = dataset.to_pandas()
                
            logger.info(f"Successfully loaded {len(self.df)} genetic variants.")
            return self.df
        except Exception as e:
            logger.error(f"Failed to fetch genetic data: {e}")
            return None

    def get_top_hits(self, p_value_col="p", threshold=5e-8):
        """
        Filters the data for genome-wide significant hits.
        
        Args:
            p_value_col: Column name containing p-values
            threshold: Significance threshold (default: 5e-8)
            
        Returns:
            pd.DataFrame: Significant hits or empty DataFrame
        """
        if self.df is not None and p_value_col in self.df.columns:
            return self.df[self.df[p_value_col] < threshold]
        return pd.DataFrame()

    def get_column_info(self):
        """Get information about available columns in the dataset."""
        if self.df is None:
            return {}
        return {
            "columns": list(self.df.columns),
            "dtypes": self.df.dtypes.to_dict(),
            "shape": self.df.shape
        }

    def summary_stats(self):
        """Get summary statistics for the loaded dataset."""
        if self.df is None:
            return {}
        
        stats = {
            "total_variants": len(self.df),
            "columns": list(self.df.columns),
            "memory_mb": self.df.memory_usage(deep=True).sum() / 1024**2
        }
        
        # Count significant hits if p-value column exists
        for p_col in ["p", "P", "pvalue", "p_value"]:
            if p_col in self.df.columns:
                sig_count = (self.df[p_col] < 5e-8).sum()
                stats["significant_hits"] = int(sig_count)
                stats["p_value_column"] = p_col
                break
                
        return stats
