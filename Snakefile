import datetime

# 현재 시간 문자열 (main.py와 동일하게 고정)
CURRENT_TIME = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 출력 파일 경로 정의
RNDJOB_BASIC = f"crawled_data/rndjob_basic_{CURRENT_TIME}.csv"
RNDJOB_DETAIL = f"crawled_data/rndjob_detail_{CURRENT_TIME}.csv"
MILITARY_BASIC = f"crawled_data/military_jobs_basic_{CURRENT_TIME}.csv"
MILITARY_DETAIL = f"crawled_data/military_jobs_detail_{CURRENT_TIME}.csv"
PROCESSED = "crawled_data/processed_job_data.csv"

rule all:
    input:
        PROCESSED

rule rndjob_job_crawler:
    output:
        basic=RNDJOB_BASIC,
        detail=RNDJOB_DETAIL
    shell:
        """
        python src/rndjob_job_crawler.py --basic-output {output.basic} --detail-output {output.detail}
        """

rule military_job_crawler:
    output:
        basic=MILITARY_BASIC,
        detail=MILITARY_DETAIL
    shell:
        """
        python src/military_job_crawler.py --basic-output {output.basic} --detail-output {output.detail}
        """

rule process_job_data:
    input:
        military_basic=MILITARY_BASIC,
        military_detail=MILITARY_DETAIL,
        rnd_basic=RNDJOB_BASIC,
        rnd_detail=RNDJOB_DETAIL
    output:
        PROCESSED
    shell:
        """
        python src/process_job_data.py \
            --military-basic {input.military_basic} \
            --military-detail {input.military_detail} \
            --rnd-basic {input.rnd_basic} \
            --rnd-detail {input.rnd_detail} \
            --output {output}
        """