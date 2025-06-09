"""
配置管理模块 - 负责加载和解析配置文件
"""
import os
import yaml
import logging
from typing import Dict, Any, List, Optional

class ConfigManager:
    """配置管理类，负责加载和管理配置"""
    
    def __init__(self, config_dir: str):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = config_dir
        self.config: Dict[str, Any] = {}
        self.journals: Dict[str, Any] = {}
        self.keywords: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    def load_all_configs(self) -> bool:
        """
        加载所有配置文件
        
        Returns:
            bool: 是否成功加载所有配置
        """
        try:
            # 加载主配置
            main_config_path = os.path.join(self.config_dir, 'config.yaml')
            self.config = self._load_yaml(main_config_path)
            
            # 加载期刊配置
            journals_path = os.path.join(self.config_dir, 'journals.yaml')
            self.journals = self._load_yaml(journals_path)
            
            # 加载关键词配置
            keywords_path = os.path.join(self.config_dir, 'keywords.yaml')
            self.keywords = self._load_yaml(keywords_path)
            
            self._setup_logging()
            self.logger.info("所有配置文件加载成功")
            return True
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return False
    
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """
        加载YAML配置文件
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            Dict: 配置字典
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
            yaml.YAMLError: YAML解析错误时抛出
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                return yaml.safe_load(file) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"解析YAML文件失败 {file_path}: {str(e)}")
    
    def _setup_logging(self) -> None:
        """设置日志配置"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'app.log')
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def get_email_config(self) -> Dict[str, Any]:
        """获取邮件配置"""
        return self.config.get('email', {})
    
    def get_run_config(self) -> Dict[str, Any]:
        """获取运行配置"""
        return self.config.get('run', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.config.get('storage', {})
    
    def get_proxy_config(self) -> Dict[str, Any]:
        """获取代理配置"""
        return self.config.get('proxy', {})
    
    def get_keywords(self) -> List[str]:
        """获取关键词列表"""
        return self.keywords.get('keywords', [])
    
    def get_keyword_matching_config(self) -> Dict[str, Any]:
        """获取关键词匹配配置"""
        return self.keywords.get('matching', {})
    
    def get_api_sources(self) -> Dict[str, Any]:
        """获取API类型数据源配置"""
        return self.journals.get('api_sources', {})
    
    def get_rss_sources(self) -> Dict[str, Any]:
        """获取RSS类型数据源配置"""
        return self.journals.get('rss_sources', {})
    
    def get_web_sources(self) -> Dict[str, Any]:
        """获取网页爬取类型数据源配置"""
        return self.journals.get('web_sources', {})
    
    def get_all_sources(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据源配置"""
        all_sources = {}
        all_sources.update(self.get_api_sources())
        all_sources.update(self.get_rss_sources())
        all_sources.update(self.get_web_sources())
        return all_sources
    
    def get_source_config(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定数据源的配置
        
        Args:
            source_id: 数据源ID
            
        Returns:
            Dict or None: 数据源配置，不存在时返回None
        """
        return self.get_all_sources().get(source_id)
