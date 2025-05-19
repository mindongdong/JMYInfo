import pandas as pd
import ast
import re
from datetime import datetime

def process_military_jobs(basic_file, detail_file):
    # Read the CSV files
    basic_df = pd.read_csv(basic_file)
    detail_df = pd.read_csv(detail_file)
    
    # Merge the dataframes
    merged_df = pd.merge(basic_df, detail_df, on='상세정보_URL', how='inner')
    
    # Create the final dataframe with required columns
    final_df = pd.DataFrame()
    
    # Map the columns according to requirements
    final_df['company_name'] = merged_df['업체명_x']
    final_df['post_name'] = merged_df['채용제목']
    final_df['registration_date'] = merged_df['작성일']
    final_df['deadline'] = merged_df['마감일']
    final_df['qualification_agent'] = merged_df['요원형태']
    final_df['qualification_education'] = merged_df['최종학력']
    final_df['qualification_career'] = merged_df['자격요원']
    final_df['region'] = merged_df['주소']
    final_df['Field'] = merged_df['담당업무']
    final_df['keywords_list'] = merged_df['비고']
    final_df['source_info'] = merged_df['상세정보_URL']
    final_df['source_type'] = 'military'  # Add source type for military jobs
    
    return final_df

def process_rnd_jobs(basic_file, detail_file):
    # Read the CSV files
    basic_df = pd.read_csv(basic_file)
    detail_df = pd.read_csv(detail_file)
    
    # Merge the dataframes
    merged_df = pd.merge(basic_df, detail_df, on='상세정보_URL', how='inner')
    
    # Create the final dataframe with required columns
    final_df = pd.DataFrame()
    
    # Map the columns according to requirements
    final_df['company_name'] = merged_df['기업명']
    final_df['post_name'] = merged_df['공고명']
    final_df['registration_date'] = merged_df['등록일']
    final_df['deadline'] = merged_df['마감일']
    
    # Use detail_df columns directly for education, career, region
    final_df['qualification_education'] = merged_df['학력']
    final_df['qualification_career'] = merged_df['경력']
    final_df['region'] = merged_df['지역']
    
    # Extract employment type from 근무환경
    def extract_employment_type(x):
        try:
            env_dict = ast.literal_eval(x)
            return env_dict.get('고용형태', '')
        except:
            return ''
    final_df['qualification_agent'] = merged_df['근무환경'].apply(extract_employment_type)
    
    final_df['Field'] = merged_df['모집_분야_및_인원']
    
    # Combine 담당업무, 자격사항, and 우대사항 for keywords
    def combine_keywords(row):
        keywords = []
        try:
            if isinstance(row['담당업무'], str):
                keywords.extend(ast.literal_eval(row['담당업무']))
            if isinstance(row['자격사항'], str):
                keywords.extend(ast.literal_eval(row['자격사항']))
            if isinstance(row['우대사항'], str):
                keywords.extend(ast.literal_eval(row['우대사항']))
        except:
            pass
        return keywords
    final_df['keywords_list'] = merged_df.apply(combine_keywords, axis=1)
    final_df['source_info'] = merged_df['상세정보_URL']
    final_df['source_type'] = 'rndjob'  # Add source type for RND jobs
    
    return final_df

def main():
    # Process military jobs
    military_basic = 'crawling_results/military_jobs_basic_20250425_162549.csv'
    military_detail = 'crawling_results/military_jobs_detail_20250425_162549.csv'
    military_df = process_military_jobs(military_basic, military_detail)
    
    # Process RND jobs
    rnd_basic = 'crawling_results/rndjob_basic_20250516_132248.csv'
    rnd_detail = 'crawling_results/rndjob_detail_20250516_132248.csv'
    rnd_df = process_rnd_jobs(rnd_basic, rnd_detail)
    
    # Combine both dataframes
    final_df = pd.concat([military_df, rnd_df], ignore_index=True)
    
    # Save the final result
    final_df.to_csv('processed_job_data.csv', index=False, encoding='utf-8-sig')
    print("Data processing completed. Results saved to 'processed_job_data.csv'")

if __name__ == "__main__":
    main() 