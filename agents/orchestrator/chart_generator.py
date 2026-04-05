"""
Chart Generator - Creates visualizations from analysis results.
Single responsibility: Generate and save charts.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Generates charts from analysis results.
    Delegates to the visualization agent.
    
    Features:
    - Automatic chart generation from tool results
    - Specialized product forecast charts
    - Batch chart generation
    - Error handling per chart
    - Support for Series and DataFrame visualizations
    """
    
    def __init__(self, viz_agent):
        """
        Initialize the Chart Generator.
        
        Args:
            viz_agent: VisualizationAgent instance for rendering charts
        """
        self.viz = viz_agent
        self._generated_charts: Dict[str, str] = {}  # Store name -> filename
    
    def generate_charts(self, raw_results: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate all applicable charts from raw results.
        
        Args:
            raw_results: Dictionary of raw tool results
            
        Returns:
            Dictionary mapping chart names to filenames (not full paths)
        """
        charts: Dict[str, str] = {}
        
        if not raw_results:
            logger.debug("No raw results provided for chart generation")
            return charts
        
        try:
            # Generate standard charts via visualization agent
            # This returns Dict[str, str] with full paths
            chart_paths = self.viz.generate_from_results(raw_results)
            
            # Convert full paths to just filenames for API compatibility
            for chart_name, full_path in chart_paths.items():
                if full_path:
                    filename = os.path.basename(full_path)
                    charts[chart_name] = filename
                    self._generated_charts[chart_name] = filename
                    logger.info(f"Chart generated: {chart_name} -> {filename}")
            
            # Log summary
            if charts:
                logger.info(f"Generated {len(charts)} charts: {list(charts.keys())}")
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}", exc_info=True)
            return {}
    
    def generate_single_chart(self, tool_name: str, result: Any) -> Optional[str]:
        """
        Generate a single chart for a specific tool.
        
        Args:
            tool_name: Name of the tool that produced the result
            result: The result to visualize
            
        Returns:
            Filename of the generated chart or None
        """
        try:
            full_path = None
            
            if isinstance(result, pd.Series):
                if not result.empty:
                    full_path = self.viz._plot_series(result, tool_name)
                    logger.debug(f"Generated series chart for {tool_name}")
                else:
                    logger.debug(f"Skipping empty series for {tool_name}")
                    
            elif isinstance(result, pd.DataFrame):
                if not result.empty:
                    full_path = self.viz._plot_dataframe(result, tool_name)
                    logger.debug(f"Generated dataframe chart for {tool_name}")
                else:
                    logger.debug(f"Skipping empty dataframe for {tool_name}")
            
            if full_path:
                filename = os.path.basename(full_path)
                self._generated_charts[tool_name] = filename
                return filename
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating chart for {tool_name}: {e}")
            return None
    
    def generate_batch_charts(self, results: List[tuple]) -> Dict[str, str]:
        """
        Generate charts for multiple tools in batch.
        
        Args:
            results: List of (tool_name, result) tuples
            
        Returns:
            Dictionary mapping chart names to filenames
        """
        charts: Dict[str, str] = {}
        
        for tool_name, result in results:
            filename = self.generate_single_chart(tool_name, result)
            if filename:
                charts[tool_name] = filename
        
        return charts
    
    def get_generated_charts(self) -> Dict[str, str]:
        """
        Get dictionary of generated chart names to filenames.
        
        Returns:
            Dictionary of chart names and their filenames
        """
        return self._generated_charts.copy()
    
    def has_charts(self) -> bool:
        """
        Check if any charts have been generated.
        
        Returns:
            True if charts exist
        """
        return len(self._generated_charts) > 0
    
    def clear_generated_charts(self) -> None:
        """Clear the list of generated chart names."""
        self._generated_charts.clear()
        logger.debug("Cleared generated charts list")
    
    def is_chart_generated(self, chart_name: str) -> bool:
        """
        Check if a specific chart has been generated.
        
        Args:
            chart_name: Name of the chart to check
            
        Returns:
            True if the chart was generated
        """
        return chart_name in self._generated_charts
    
    def get_chart_summary(self) -> Dict[str, Any]:
        """
        Get a summary of generated charts.
        
        Returns:
            Dictionary with chart statistics
        """
        return {
            'total_charts': len(self._generated_charts),
            'chart_names': list(self._generated_charts.keys()),
            'has_charts': self.has_charts()
        }


__all__ = ['ChartGenerator']