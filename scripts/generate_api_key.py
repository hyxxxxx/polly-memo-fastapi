#!/usr/bin/env python3
"""
API密钥生成脚本
用于生成安全的随机API密钥
"""
import secrets
import string
import sys


def generate_api_key(length: int = 32) -> str:
    """
    生成安全的随机API密钥
    
    Args:
        length: 密钥长度，默认32字符
        
    Returns:
        str: 生成的API密钥
    """
    # 使用字母、数字、连字符和下划线
    alphabet = string.ascii_letters + string.digits + "-_"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    """主函数"""
    print("🔐 Polly Memo API密钥生成器")
    print("=" * 40)
    
    # 检查命令行参数
    length = 32
    if len(sys.argv) > 1:
        try:
            length = int(sys.argv[1])
            if length < 16:
                print("⚠️  警告：密钥长度小于16可能不够安全")
        except ValueError:
            print("❌ 错误：长度必须是数字")
            sys.exit(1)
    
    # 生成多个密钥供选择
    print(f"生成长度为 {length} 的API密钥：\n")
    
    for i in range(3):
        api_key = generate_api_key(length)
        print(f"密钥 {i+1}: {api_key}")
    
    print(f"\n📝 使用方法：")
    print("1. 复制上面的一个密钥")
    print("2. 在 .env 文件中设置：")
    print("   API_KEY=your-chosen-key-here")
    print("   ENABLE_API_KEY_AUTH=true")
    print("3. 重启应用")
    
    print(f"\n🧪 测试命令：")
    sample_key = generate_api_key(length)
    print(f"curl -H \"X-API-Key: {sample_key}\" \\")
    print(f"     -X GET \"http://localhost:8000/api/v1/analysis/supported-languages\"")
    
    print(f"\n🔒 安全提醒：")
    print("- 不要在代码中硬编码API密钥")
    print("- 不要将 .env 文件提交到版本控制")
    print("- 定期轮换API密钥")
    print("- 生产环境使用HTTPS")


if __name__ == "__main__":
    main() 