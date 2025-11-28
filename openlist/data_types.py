from pydantic import BaseModel, Field

class SimpleLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    otp_key: str = Field(None, description="OTP密钥")
