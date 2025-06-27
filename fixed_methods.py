"""
Fixed methods for SurrealUserStorage class
"""

# Fixed get_user_by_email method
async def get_user_by_email(self, email: str) -> Optional[User]:
    """
    通过邮箱获取用户
    
    Args:
        email: 用户邮箱
        
    Returns:
        用户对象，如果不存在则返回None
    """
    try:
        # 构建查询
        query = f"SELECT * FROM {self.table} WHERE email = '{email}'"
    
        # 执行查询
        result = self.db.execute_sql(query)
        logger.info(f"get_user_by_email 查询结果: {result}")
        
        # 处理结果
        if result and len(result) > 0:
            if isinstance(result[0], list) and len(result[0]) > 0:
                user_data = result[0][0]
            else:
                user_data = result[0]
            return User.from_dict(user_data)
        
        return None
    except Exception as e:
        logger.error(f"通过邮箱获取用户失败: {e}")
        return None

# Fixed get_user_by_provider method
async def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
    """
    通过认证提供商获取用户
    
    Args:
        provider: 认证提供商
        provider_id: 提供商用户ID
        
    Returns:
        用户对象，如果不存在则返回None
    """
    try:
        # 构建查询
        query = f"SELECT * FROM {self.table} WHERE provider = '{provider}' AND provider_id = '{provider_id}'"
    
        # 执行查询
        result = self.db.execute_sql(query)
        logger.info(f"get_user_by_provider 查询结果: {result}")
        
        # 处理结果
        if result and len(result) > 0:
            if isinstance(result[0], list) and len(result[0]) > 0:
                user_data = result[0][0]
            else:
                user_data = result[0]
            return User.from_dict(user_data)
        
        return None
    except Exception as e:
        logger.error(f"通过提供商获取用户失败: {e}")
        return None
