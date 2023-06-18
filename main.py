#写一个完整的python程序，处理m3u格式的iptv列表，采用并行的方式测试每个地址，按照速度排序，结果输出成m3u格式。
#要求显示当前进度，可以随时中断并恢复进度，要求总的测试时间尽可能小

import concurrent.futures
import requests
import time
from tqdm import tqdm
import signal
import pickle

# 存储进度的文件
progress_file = 'progress.pkl'


# 保存进度
def save_progress(results):
    with open(progress_file, 'wb') as f:
        pickle.dump(results, f)


# 读取进度
def load_progress():
    try:
        with open(progress_file, 'rb') as f:
            return pickle.load(f)
    except:
        return []


# 测试URL的函数
def test_url(url):
    start_time = time.time()
    try:
        response = requests.get(url, timeout=5)
        time_taken = time.time() - start_time
        return (url, time_taken)
    except:
        return (url, float('inf'))


# 处理m3u文件
def process_m3u_file(file_path):
    # 读取已测试的结果
    results = load_progress()

    # 读取所有URL
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file if line.strip() and not line.startswith('#')]

    # 设置信号处理函数,保存进度并退出
    def signal_handler(signal, frame):
        save_progress(results)
        executor.shutdown()
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
        # 使用tqdm显示进度条
        with tqdm(total=len(urls)) as pbar:
            for url in urls:
                if url not in results:
                    future = executor.submit(test_url, url)
                    results.append(future)
                pbar.update(1)

                # 等待所有任务完成
        for future in concurrent.futures.as_completed(results):
            url, time_taken = future.result()
            print(f"Tested {url}, time: {time_taken}")

    # 按照速度排序结果
    results.sort(key=lambda x: x[1])

    # 输出结果到output.m3u文件
    with open('output.m3u', 'w') as file:
        for url, _ in results:
            file.write(f"{url}\n")

    # 删除进度文件
    if os.path.exists(progress_file):
        os.remove(progress_file)


if __name__ == "__main__":
    process_m3u_file('index.nsfw.m3u')
