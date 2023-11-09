import os
import requests
from urllib.parse import urlparse, unquote
from serbia_scripts.utils import print_with_session_number, print_exception

def handle_image(url, local_path, session, session_number, CHUNK_SIZE):
    try:
        retries = Retry(total=5,
                        backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504],
                        allowed_methods=["HEAD", "GET"])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        if local_path.startswith('//'):
            local_path = local_path[1:]
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        head = session.head(url, timeout=10)
        if head.status_code == 200:
            print_with_session_number(session_number, f"Image exists: {url}")

            with open(local_path, 'wb') as out_file:
                response = session.get(url, stream=True, timeout=10)
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    out_file.write(chunk)
            print_with_session_number(session_number, f"Image downloaded: {url}")
            return True
        else:
            return False
    except requests.RequestException as e:
        print_exception(session_number, e)
        return False

def parse_image_numbers(df, session_number):
    stats = {
        'smallest_image': None,
        'largest_image': None,
        'digit_format': 'unknown',
        'dup_status': 'nodups',
        'late_start': False,
        'gaps_found': False,
        'total_images': len(df),
        'existing_images': 0,
        'saved_images': 0
    }

    seen_numbers = set()

    for _, row in df.iterrows():
        image_url = row['URL']
        image_number = int(os.path.splitext(os.path.basename(image_url))[0])
        seen_numbers.add(image_number)

    if seen_numbers:
        stats['smallest_image'] = min(seen_numbers)
        stats['largest_image'] = max(seen_numbers)
        stats['digit_format'] = '3n' if all(len(str(num)) == 3 for num in seen_numbers) else '4n' if all(len(str(num)) == 4 for num in seen_numbers) else 'mixed'
        stats['dup_status'] = 'dups' if len(seen_numbers) < stats['total_images'] else 'nodups'
        stats['late_start'] = min(seen_numbers) != 1
        stats['gaps_found'] = len(seen_numbers) != stats['largest_image'] - stats['smallest_image'] + 1

    print_with_session_number(session_number, f"Stats parsed: {stats}")
    return stats

def update_status_and_save_csv(df, csv_path, index, status, session_number):
    status_map = {'Not Found': 'N', 'Downloaded': 'D', 'Exists': 'E'}
    df.at[index, 'Status'] = status_map[status]
    df.to_csv(csv_path, index=False)

    url_parts = urlparse(df.at[index, 'URL'])
    url_path_parts = url_parts.path.split('/')
    settlement, religion, year, state = url_path_parts[-5], url_path_parts[-4], url_path_parts[-3], url_path_parts[-2]

    religion_weight = df.at[index, "religion_weight"]
    year_weight = df.at[index, "year_weight"]
    state_weight = df.at[index, "state_weight"]
    overall_weight = df.at[index, "Weight"]

    print_status_with_color(session_number, f"Row {index} ({settlement}/{religion}/{year}/{state}/{os.path.basename(url_parts.path)}) ", status, religion_weight=religion_weight, year_weight=year_weight, state_weight=state_weight, overall_weight=overall_weight)
