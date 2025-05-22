import pandas as pd
import ast
import re
from datetime import datetime
import os
import argparse

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

def update_job_data(new_df):
    """Update job data with status and update date tracking"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add update_date and status columns to new data
    new_df['update_date'] = current_time
    new_df['status'] = 'new'
    
    # Check if existing processed data exists
    if os.path.exists('processed_job_data.csv'):
        existing_df = pd.read_csv('processed_job_data.csv')
        
        # Create a unique identifier for each job posting
        new_df['job_id'] = new_df['company_name'] + '_' + new_df['post_name'] + '_' + new_df['source_info']
        existing_df['job_id'] = existing_df['company_name'] + '_' + existing_df['post_name'] + '_' + existing_df['source_info']
        
        # Find new entries
        new_entries = new_df[~new_df['job_id'].isin(existing_df['job_id'])]
        
        # Find updated entries
        updated_entries = new_df[new_df['job_id'].isin(existing_df['job_id'])]
        updated_entries['status'] = 'updated'
        
        # Find unchanged entries
        unchanged_entries = existing_df[~existing_df['job_id'].isin(new_df['job_id'])]
        unchanged_entries['status'] = 'unchanged'
        
        # Combine all entries
        final_df = pd.concat([new_entries, updated_entries, unchanged_entries], ignore_index=True)
        
        # Drop the temporary job_id column
        final_df = final_df.drop('job_id', axis=1)
        
        return final_df
    else:
        # If no existing data, all entries are new
        return new_df

def main():
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Process job data from crawled files')
        parser.add_argument('--military-basic', required=True, help='Path to military jobs basic CSV file')
        parser.add_argument('--military-detail', required=True, help='Path to military jobs detail CSV file')
        parser.add_argument('--rnd-basic', required=True, help='Path to RND jobs basic CSV file')
        parser.add_argument('--rnd-detail', required=True, help='Path to RND jobs detail CSV file')
        parser.add_argument('--output', required=True, help='Path to output processed CSV file')
        
        args = parser.parse_args()
        
        # Process military jobs
        military_df = process_military_jobs(args.military_basic, args.military_detail)
        
        # Process RND jobs
        rnd_df = process_rnd_jobs(args.rnd_basic, args.rnd_detail)
        
        # Combine both dataframes
        combined_df = pd.concat([military_df, rnd_df], ignore_index=True)
        
        # Convert date columns with mixed formats
        for date_col in ['registration_date', 'deadline']:
            combined_df[date_col] = pd.to_datetime(combined_df[date_col], format='mixed')
        
        # Update with status and update date
        final_df = update_job_data(combined_df)
        
        # Save the final result
        final_df.to_csv(args.output, index=False, encoding='utf-8-sig')
        print(f"Data processing completed. Results saved to '{args.output}'")
        
        # Print statistics
        status_counts = final_df['status'].value_counts()
        print("\nUpdate Statistics:")
        for status, count in status_counts.items():
            print(f"{status}: {count} entries")
            
    except Exception as e:
        print(f"An error occurred during processing: {e}")
        return

if __name__ == "__main__":
    main() 