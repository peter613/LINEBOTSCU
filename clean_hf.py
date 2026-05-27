import os
from huggingface_hub import HfApi

# 確保有設定 token 或已經使用 huggingface-cli login
api = HfApi()

repo_id = "peter613/SCULINEBOT"

try:
    # 注意：Hugging Face Space 的 repo_type 是 "space"
    repo_files = api.list_repo_files(repo_id=repo_id, repo_type="space")
    print(f"Found {len(repo_files)} files. Starting deletion...")

    for file_path in repo_files:
        # 保留 .gitattributes
        if file_path in [".gitattributes"]:
            continue
        
        api.delete_file(
            path_in_repo=file_path,
            repo_id=repo_id,
            repo_type="space"
        )
        print(f"已刪除: {file_path}")
        
    print("✅ 全部舊檔案清理完畢！")
except Exception as e:
    print(f"❌ 發生錯誤: {e}")
