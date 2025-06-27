"""
Fixed methods for SurrealUserStorage class
"""

# Fixed get_user method
async def get_user(self, user_id: str) -> Optional[User]:
    """
    获取用户
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户对象，如果不存在则返回None
    """
    try:
        # 直接获取用户记录
        result = self.db.execute_sql(f"SELECT * FROM {self.table} WHERE id = '{user_id}'")
        
        # 处理结果
        if result and len(result) > 0:
            user_data = result[0]
            return User.from_dict(user_data)
        
        # 如果直接获取失败，尝试使用另一种查询格式
        query = f"SELECT * FROM {self.table} WHERE id = '{user_id}';"
        
        # 执行查询
        result = self.db.execute_sql(query)
        
        # 处理结果
        if result and len(result) > 0:
            user_data = result[0]
            return User.from_dict(user_data)
        
        return None
    except Exception as e:
        logger.error(f"获取用户失败: {e}")
        return None

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
        
        # 处理结果
        if result and len(result) > 0 and len(result[0]) > 0:
            user_data = result[0][0]
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
        
        # 处理结果
        if result and len(result) > 0 and len(result[0]) > 0:
            user_data = result[0][0]
            return User.from_dict(user_data)
        
        return None
    except Exception as e:
        logger.error(f"通过提供商获取用户失败: {e}")
        return None

# Fixed create_user method
async def create_user(self, user: User) -> User:
    """
    创建用户
    
    Args:
        user: 用户对象
        
    Returns:
        创建的用户对象
    """
    try:
        # 确保用户有ID
        if not user.id:
            user.id = str(uuid.uuid4())
        
        # 转换为字典
        user_dict = user.to_dict()
        
        # 执行创建 - 使用 INSERT 语句
        user_json = json.dumps(user_dict)
        query = f"INSERT INTO {self.table} {user_json};"
        result = self.db.execute_sql(query)
        
        # 处理结果
        if result and len(result) > 0:
            created_user = result[0]
            return User.from_dict(created_user)
        
        return user
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        return user
