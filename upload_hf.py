from huggingface_hub import HfApi

api = HfApi()
repo_id = "peter613/SCULINEBOT"

print("開始上傳最新的程式碼至 Hugging Face Space...")
try:
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=[".git*", ".env", "__pycache__", "clean_hf.py", "upload_hf.py"]
    )
    print("✅ 程式碼上傳成功！")
except Exception as e:
    print(f"上傳失敗: {e}")
