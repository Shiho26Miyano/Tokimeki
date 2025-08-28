"""
FutureQuant Trader MLflow Service - Enhanced Experiment Tracking
"""
import logging
import os
import json
import pickle
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import mlflow
import mlflow.pytorch
import mlflow.sklearn
import mlflow.xgboost
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class FutureQuantMLflowService:
    """Enhanced MLflow service for FutureQuant Trader experiment tracking and model management"""
    
    def __init__(self, tracking_uri: str = None, registry_uri: str = None):
        """Initialize MLflow service"""
        # Set tracking URI
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        elif os.getenv("MLFLOW_TRACKING_URI"):
            mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
        else:
            # Default local tracking
            mlflow.set_tracking_uri("sqlite:///mlflow.db")
        
        # Set registry URI
        if registry_uri:
            mlflow.set_registry_uri(registry_uri)
        elif os.getenv("MLFLOW_REGISTRY_URI"):
            mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI"))
        
        # Set experiment name
        self.experiment_name = "FutureQuant_Trader"
        self._ensure_experiment_exists()
        
        logger.info(f"MLflow service initialized with tracking URI: {mlflow.get_tracking_uri()}")
    
    def _ensure_experiment_exists(self):
        """Ensure the FutureQuant experiment exists"""
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                mlflow.create_experiment(self.experiment_name)
                logger.info(f"Created experiment: {self.experiment_name}")
            else:
                mlflow.set_experiment(self.experiment_name)
        except Exception as e:
            logger.warning(f"Could not set experiment: {str(e)}")
    
    async def start_experiment(
        self,
        experiment_name: str = None,
        run_name: str = None,
        tags: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Start a new MLflow experiment run"""
        try:
            # Set experiment
            if experiment_name:
                mlflow.set_experiment(experiment_name)
            else:
                mlflow.set_experiment(self.experiment_name)
            
            # Start run
            run = mlflow.start_run(run_name=run_name, tags=tags or {})
            
            logger.info(f"Started MLflow run: {run.info.run_id}")
            
            return {
                'success': True,
                'run_id': run.info.run_id,
                'experiment_id': run.info.experiment_id,
                'run_name': run_name or 'FutureQuant_Run'
            }
            
        except Exception as e:
            logger.error(f"Error starting experiment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def log_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log parameters for the current run"""
        try:
            mlflow.log_params(params)
            logger.info(f"Logged {len(params)} parameters")
            
            return {
                'success': True,
                'params_logged': len(params)
            }
            
        except Exception as e:
            logger.error(f"Error logging parameters: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def log_metrics(self, metrics: Dict[str, float], step: int = None) -> Dict[str, Any]:
        """Log metrics for the current run"""
        try:
            for metric_name, metric_value in metrics.items():
                if step is not None:
                    mlflow.log_metric(metric_name, metric_value, step=step)
                else:
                    mlflow.log_metric(metric_name, metric_value)
            
            logger.info(f"Logged {len(metrics)} metrics")
            
            return {
                'success': True,
                'metrics_logged': len(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error logging metrics: {str(e)}")
            return {
                'success': False,
                'error': str(e)}
    
    async def log_distributional_metrics(
        self,
        y_true: np.ndarray,
        y_pred_q10: np.ndarray,
        y_pred_q50: np.ndarray,
        y_pred_q90: np.ndarray,
        y_pred_prob: np.ndarray = None,
        y_pred_vol: np.ndarray = None,
        step: int = None
    ) -> Dict[str, Any]:
        """Log distributional forecasting metrics"""
        try:
            metrics = {}
            
            # Quantile coverage metrics
            coverage_10_90 = np.mean((y_true >= y_pred_q10) & (y_true <= y_pred_q90))
            coverage_10_50 = np.mean((y_true >= y_pred_q10) & (y_true <= y_pred_q50))
            coverage_50_90 = np.mean((y_true >= y_pred_q50) & (y_true <= y_pred_q90))
            
            metrics['coverage_10_90'] = coverage_10_90
            metrics['coverage_10_50'] = coverage_10_50
            metrics['coverage_50_90'] = coverage_50_90
            
            # Quantile regression metrics
            q10_loss = np.mean(np.maximum((y_true - y_pred_q10) * 0.1, (y_pred_q10 - y_true) * 0.9))
            q50_loss = np.mean(np.abs(y_true - y_pred_q50))
            q90_loss = np.mean(np.maximum((y_true - y_pred_q90) * 0.9, (y_pred_q90 - y_true) * 0.1))
            
            metrics['q10_pinball_loss'] = q10_loss
            metrics['q50_mae'] = q50_loss
            metrics['q90_pinball_loss'] = q90_loss
            
            # Probability metrics (if available)
            if y_pred_prob is not None:
                # Convert to binary classification
                y_binary = (y_true > y_pred_q50).astype(int)
                prob_accuracy = np.mean((y_pred_prob > 0.5) == y_binary)
                metrics['prob_accuracy'] = prob_accuracy
                
                # Log loss for probability
                eps = 1e-15
                y_pred_prob_clipped = np.clip(y_pred_prob, eps, 1 - eps)
                log_loss = -np.mean(y_binary * np.log(y_pred_prob_clipped) + 
                                  (1 - y_binary) * np.log(1 - y_pred_prob_clipped))
                metrics['prob_log_loss'] = log_loss
            
            # Volatility metrics (if available)
            if y_pred_vol is not None:
                # Volatility calibration
                vol_rmse = np.sqrt(np.mean((y_pred_vol - np.abs(y_true - y_pred_q50)) ** 2))
                metrics['vol_rmse'] = vol_rmse
                
                # Volatility correlation
                vol_corr = np.corrcoef(y_pred_vol, np.abs(y_true - y_pred_q50))[0, 1]
                if not np.isnan(vol_corr):
                    metrics['vol_correlation'] = vol_corr
            
            # Overall distributional score
            distributional_score = (coverage_10_90 * 0.4 + 
                                  (1 - q50_loss / np.std(y_true)) * 0.3 + 
                                  (1 - q10_loss / np.std(y_true)) * 0.15 + 
                                  (1 - q90_loss / np.std(y_true)) * 0.15)
            metrics['distributional_score'] = distributional_score
            
            # Log all metrics
            await self.log_metrics(metrics, step)
            
            return {
                'success': True,
                'metrics_logged': len(metrics),
                'distributional_score': distributional_score
            }
            
        except Exception as e:
            logger.error(f"Error logging distributional metrics: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def log_model(
        self,
        model: Any,
        model_name: str,
        model_type: str = "pytorch",
        conda_env: Dict[str, Any] = None,
        registered_model_name: str = None,
        artifact_path: str = None
    ) -> Dict[str, Any]:
        """Log a trained model"""
        try:
            if model_type == "pytorch":
                mlflow.pytorch.log_model(
                    model,
                    artifact_path=artifact_path or "model",
                    registered_model_name=registered_model_name,
                    conda_env=conda_env
                )
            elif model_type == "sklearn":
                mlflow.sklearn.log_model(
                    model,
                    artifact_path=artifact_path or "model",
                    registered_model_name=registered_model_name,
                    conda_env=conda_env
                )
            elif model_type == "xgboost":
                mlflow.xgboost.log_model(
                    model,
                    artifact_path=artifact_path or "model",
                    registered_model_name=registered_model_name,
                    conda_env=conda_env
                )
            else:
                # Generic model logging
                mlflow.log_artifact(
                    model,
                    artifact_path=artifact_path or "model"
                )
            
            logger.info(f"Logged model: {model_name} ({model_type})")
            
            return {
                'success': True,
                'model_name': model_name,
                'model_type': model_type,
                'artifact_path': artifact_path or "model"
            }
            
        except Exception as e:
            logger.error(f"Error logging model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def log_artifact(self, local_path: str, artifact_path: str = None) -> Dict[str, Any]:
        """Log an artifact file"""
        try:
            mlflow.log_artifact(local_path, artifact_path)
            logger.info(f"Logged artifact: {local_path}")
            
            return {
                'success': True,
                'artifact_path': artifact_path or local_path
            }
            
        except Exception as e:
            logger.error(f"Error logging artifact: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def log_feature_importance(
        self,
        feature_names: List[str],
        importance_scores: np.ndarray,
        importance_type: str = "feature_importance"
    ) -> Dict[str, Any]:
        """Log feature importance information"""
        try:
            # Create feature importance DataFrame
            feature_df = pd.DataFrame({
                'feature_name': feature_names,
                'importance_score': importance_scores
            }).sort_values('importance_score', ascending=False)
            
            # Save to temporary file
            temp_path = f"/tmp/feature_importance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            feature_df.to_csv(temp_path, index=False)
            
            # Log as artifact
            await self.log_artifact(temp_path, "feature_importance.csv")
            
            # Log top features as metrics
            top_features = feature_df.head(10)
            for _, row in top_features.iterrows():
                metric_name = f"feature_importance_{row['feature_name']}"
                mlflow.log_metric(metric_name, row['importance_score'])
            
            # Clean up
            os.remove(temp_path)
            
            logger.info(f"Logged feature importance for {len(feature_names)} features")
            
            return {
                'success': True,
                'features_logged': len(feature_names),
                'top_features': top_features['feature_name'].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error logging feature importance: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def log_training_history(
        self,
        history: Dict[str, List[float]],
        plot: bool = True
    ) -> Dict[str, Any]:
        """Log training history and optionally create plots"""
        try:
            # Log final metrics
            final_metrics = {f"final_{key}": values[-1] for key, values in history.items()}
            await self.log_metrics(final_metrics)
            
            # Log training curves
            for metric_name, values in history.items():
                for step, value in enumerate(values):
                    mlflow.log_metric(f"train_{metric_name}", value, step=step)
            
            # Create and log training plots if requested
            if plot:
                try:
                    import matplotlib.pyplot as plt
                    
                    fig, axes = plt.subplots(1, len(history), figsize=(5*len(history), 4))
                    if len(history) == 1:
                        axes = [axes]
                    
                    for i, (metric_name, values) in enumerate(history.items()):
                        axes[i].plot(values)
                        axes[i].set_title(f'Training {metric_name}')
                        axes[i].set_xlabel('Epoch')
                        axes[i].set_ylabel(metric_name)
                        axes[i].grid(True)
                    
                    plt.tight_layout()
                    
                    # Save and log plot
                    plot_path = f"/tmp/training_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    
                    await self.log_artifact(plot_path, "training_history.png")
                    os.remove(plot_path)
                    
                except ImportError:
                    logger.warning("Matplotlib not available, skipping training plots")
            
            logger.info(f"Logged training history with {len(history)} metrics")
            
            return {
                'success': True,
                'metrics_logged': len(history),
                'final_metrics': final_metrics
            }
            
        except Exception as e:
            logger.error(f"Error logging training history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def end_experiment(self) -> Dict[str, Any]:
        """End the current MLflow run"""
        try:
            mlflow.end_run()
            logger.info("Ended MLflow run")
            
            return {
                'success': True,
                'message': 'Experiment ended successfully'
            }
            
        except Exception as e:
            logger.error(f"Error ending experiment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_experiment_runs(
        self,
        experiment_name: str = None,
        filter_string: str = None,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """Get experiment runs"""
        try:
            # Set experiment
            if experiment_name:
                mlflow.set_experiment(experiment_name)
            else:
                mlflow.set_experiment(self.experiment_name)
            
            # Get experiment
            experiment = mlflow.get_experiment_by_name(experiment_name or self.experiment_name)
            if not experiment:
                return {
                    'success': False,
                    'error': f"Experiment {experiment_name or self.experiment_name} not found"
                }
            
            # Search runs
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=filter_string,
                max_results=max_results
            )
            
            # Convert to list of dicts
            runs_data = []
            for _, run in runs.iterrows():
                run_data = {
                    'run_id': run['run_id'],
                    'run_name': run.get('tags.mlflow.runName', 'Unknown'),
                    'status': run['status'],
                    'start_time': run['start_time'],
                    'end_time': run['end_time'],
                    'metrics': {col: run[col] for col in run.columns if col.startswith('metrics.')},
                    'params': {col: run[col] for col in run.columns if col.startswith('params.')},
                    'tags': {col: run[col] for col in run.columns if col.startswith('tags.')}
                }
                runs_data.append(run_data)
            
            return {
                'success': True,
                'experiment_name': experiment_name or self.experiment_name,
                'total_runs': len(runs_data),
                'runs': runs_data
            }
            
        except Exception as e:
            logger.error(f"Error getting experiment runs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_run_details(self, run_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific run"""
        try:
            run = mlflow.get_run(run_id)
            
            run_data = {
                'run_id': run.info.run_id,
                'experiment_id': run.info.experiment_id,
                'run_name': run.data.tags.get('mlflow.runName', 'Unknown'),
                'status': run.info.status,
                'start_time': run.info.start_time,
                'end_time': run.info.end_time,
                'metrics': run.data.metrics,
                'params': run.data.params,
                'tags': run.data.tags
            }
            
            return {
                'success': True,
                'run': run_data
            }
            
        except Exception as e:
            logger.error(f"Error getting run details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def compare_runs(
        self,
        run_ids: List[str],
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Compare multiple runs"""
        try:
            if len(run_ids) < 2:
                return {
                    'success': False,
                    'error': 'Need at least 2 runs to compare'
                }
            
            comparison_data = []
            
            for run_id in run_ids:
                run_details = await self.get_run_details(run_id)
                if run_details['success']:
                    run_data = run_details['run']
                    
                    # Extract metrics
                    run_metrics = {}
                    if metrics:
                        for metric in metrics:
                            run_metrics[metric] = run_data['metrics'].get(metric, None)
                    else:
                        run_metrics = run_data['metrics']
                    
                    comparison_data.append({
                        'run_id': run_id,
                        'run_name': run_data['run_name'],
                        'metrics': run_metrics,
                        'params': run_data['params']
                    })
            
            # Create comparison summary
            comparison_summary = {}
            if comparison_data and metrics:
                for metric in metrics:
                    values = [run['metrics'].get(metric) for run in comparison_data 
                             if run['metrics'].get(metric) is not None]
                    if values:
                        comparison_summary[metric] = {
                            'min': min(values),
                            'max': max(values),
                            'mean': np.mean(values),
                            'std': np.std(values)
                        }
            
            return {
                'success': True,
                'runs_compared': len(comparison_data),
                'comparison_data': comparison_data,
                'comparison_summary': comparison_summary
            }
            
        except Exception as e:
            logger.error(f"Error comparing runs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def register_model(
        self,
        model_uri: str,
        name: str,
        description: str = None,
        tags: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Register a model in the model registry"""
        try:
            # Register model
            model_version = mlflow.register_model(
                model_uri=model_uri,
                name=name,
                description=description,
                tags=tags or {}
            )
            
            logger.info(f"Registered model: {name} version {model_version.version}")
            
            return {
                'success': True,
                'model_name': name,
                'version': model_version.version,
                'model_uri': model_uri
            }
            
        except Exception as e:
            logger.error(f"Error registering model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_registered_models(self, name: str = None) -> Dict[str, Any]:
        """Get registered models"""
        try:
            if name:
                # Get specific model
                model = mlflow.get_registered_model(name)
                versions = mlflow.search_model_versions(f"name='{name}'")
                
                model_data = {
                    'name': model.name,
                    'description': model.description,
                    'latest_versions': [v.version for v in model.latest_versions],
                    'versions': [{
                        'version': v.version,
                        'status': v.status,
                        'run_id': v.run_id,
                        'created_at': v.creation_timestamp
                    } for v in versions]
                }
                
                return {
                    'success': True,
                    'model': model_data
                }
            else:
                # Get all models
                models = mlflow.list_registered_models()
                
                models_data = []
                for model in models:
                    models_data.append({
                        'name': model.name,
                        'description': model.description,
                        'latest_versions': [v.version for v in model.latest_versions]
                    })
                
                return {
                    'success': True,
                    'total_models': len(models_data),
                    'models': models_data
                }
                
        except Exception as e:
            logger.error(f"Error getting registered models: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def load_model(self, model_uri: str, model_type: str = "pytorch") -> Dict[str, Any]:
        """Load a model from MLflow"""
        try:
            if model_type == "pytorch":
                model = mlflow.pytorch.load_model(model_uri)
            elif model_type == "sklearn":
                model = mlflow.sklearn.load_model(model_uri)
            elif model_type == "xgboost":
                model = mlflow.xgboost.load_model(model_uri)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported model type: {model_type}"
                }
            
            return {
                'success': True,
                'model': model,
                'model_type': model_type,
                'model_uri': model_uri
            }
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_experiment_summary(self, experiment_name: str = None) -> Dict[str, Any]:
        """Get summary statistics for an experiment"""
        try:
            # Get experiment runs
            runs_result = await self.get_experiment_runs(experiment_name, max_results=1000)
            
            if not runs_result['success']:
                return runs_result
            
            runs = runs_result['runs']
            
            if not runs:
                return {
                    'success': True,
                    'experiment_name': experiment_name or self.experiment_name,
                    'total_runs': 0,
                    'summary': {}
                }
            
            # Calculate summary statistics
            summary = {
                'total_runs': len(runs),
                'completed_runs': len([r for r in runs if r['status'] == 'FINISHED']),
                'failed_runs': len([r for r in runs if r['status'] == 'FAILED']),
                'running_runs': len([r for r in runs if r['status'] == 'RUNNING'])
            }
            
            # Get common metrics
            all_metrics = set()
            for run in runs:
                all_metrics.update(run['metrics'].keys())
            
            # Calculate metric statistics
            metric_stats = {}
            for metric in all_metrics:
                values = [run['metrics'].get(metric) for run in runs 
                         if run['metrics'].get(metric) is not None]
                if values:
                    metric_stats[metric] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'mean': np.mean(values),
                        'std': np.std(values)
                    }
            
            summary['metric_statistics'] = metric_stats
            
            return {
                'success': True,
                'experiment_name': experiment_name or self.experiment_name,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error getting experiment summary: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def export_experiment(
        self,
        experiment_name: str = None,
        export_path: str = None
    ) -> Dict[str, Any]:
        """Export experiment data"""
        try:
            # Get experiment runs
            runs_result = await self.get_experiment_runs(experiment_name, max_results=10000)
            
            if not runs_result['success']:
                return runs_result
            
            # Prepare export data
            export_data = {
                'experiment_name': experiment_name or self.experiment_name,
                'export_timestamp': datetime.now().isoformat(),
                'runs': runs_result['runs']
            }
            
            # Export to file
            if not export_path:
                export_path = f"/tmp/futurequant_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported experiment to: {export_path}")
            
            return {
                'success': True,
                'export_path': export_path,
                'runs_exported': len(runs_result['runs'])
            }
            
        except Exception as e:
            logger.error(f"Error exporting experiment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
