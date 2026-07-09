from apscheduler.schedulers.blocking import BlockingScheduler
import fetcher
import processor
import analyzer
import config

def daily_job():
    print("[scheduler] 开始每日抓取任务...")
    articles = fetcher.fetch_all()
    processor.save_articles(articles)
    analyzer.run_analysis()
    print("[scheduler] 每日任务完成")

if __name__ == "__main__":
    processor.init_db()
    scheduler = BlockingScheduler()
    scheduler.add_job(daily_job, "cron", hour=config.FETCH_HOUR, minute=0)
    print(f"[scheduler] 定时任务已启动，每天 {config.FETCH_HOUR}:00 自动运行")
    print("[scheduler] 按 Ctrl+C 停止")
    scheduler.start()
