import os
import re
import urllib.request
import shutil
import argparse
import mistune
import bs4 as BeautifulSoup


def download_file(link, location, name):
    try:
        response = urllib.request.urlopen(link, timeout=500)
        file = open(os.path.join(location, name), 'wb')
        file_size = int(response.info()['Content-Length'])
        downloaded_size = 0
        block_size = 8192
        while downloaded_size < file_size:
            buffer = response.read(block_size)
            if not buffer:
                break
            downloaded_size += len(buffer)
            file.write(buffer)
        file.close()
    except urllib.error.HTTPError:
        print('>>> Error 404: cannot be downloaded!\n')
        raise
    # except socket.timeout:
    #     print(" ".join(("can't download", link, "due to connection timeout!")) )
    except Exception as e:
        print('Fail to download:\n' + e.message)
        raise

def download_pdf(link, location, name):
    try:
        response = urllib.request.urlopen(link, timeout=500)
        file = open(os.path.join(location, name), 'wb')
        file.write(response.read())
        file.close()
    except urllib.error.HTTPError:
        print('>>> Error 404: cannot be downloaded!\n') 
        raise   
    except socket.timeout:
        print(" ".join(("can't download", link, "due to connection timeout!")) )
    except Exception as e:
        print('Fail to download:\n' + e.message)

def clean_pdf_link(link):
    if 'arxiv' in link:
        link = link.replace('abs', 'pdf')   
        if not(link.endswith('.pdf')):
            link = '.'.join((link, 'pdf'))
    return link

def clean_text(text, replacements = {' ': '_', '/': '_', '.': '', '"': '', ':': '_', '\\': '_', '*': '_', '?': '_', '<': '_', '>':'_'}):
    for key, rep in replacements.items():
        text = text.replace(key, rep)
    return text    

def print_title(title, pattern = "-"):
    print('\n'.join(("", title, pattern * len(title)))) 

def get_extension(link):
    extension = os.path.splitext(link)[1][1:]
    if extension in ['pdf', 'html']:
        return extension
    if 'pdf' in extension:
        return 'pdf'    
    return 'pdf'    

def shorten_title(title):
    m1 = re.search('[[0-9]*]', title)
    m2 = re.search('".*"', title)
    if m1:
        title = m1.group(0)
    if m2:
        title = ' '.join((title, m2.group(0)))   
    return title[:50] + ' [...]'    


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Download all the PDF/HTML links into README.md')
    parser.add_argument('-d', action="store", dest="directory")
    parser.add_argument('--no-html', action="store_true", dest="nohtml", default = False)
    parser.add_argument('--overwrite', action="store_true", default = False)    
    results = parser.parse_args()

    output_directory = 'pdfs' if results.directory is None else results.directory

    forbidden_extensions = ['html', 'htm'] if results.nohtml else []

    if results.overwrite and os.path.exists(output_directory):
        shutil.rmtree(output_directory)

    with open('README.md', encoding='utf8') as readme:
        readme_html = mistune.markdown(readme.read())
        readme_soup = BeautifulSoup.BeautifulSoup(readme_html, "html.parser")

    point = readme_soup.find_all('h1')[0]

    failures = []
    while point is not None:
        if point.name:
            if re.search('h[1-2]', point.name):
                if point.name == 'h1':
                    h1_directory = os.path.join(output_directory, clean_text(point.text))
                    current_directory = h1_directory
                elif point.name == 'h2':
                    current_directory = os.path.join(h1_directory, clean_text(point.text))  
                if not os.path.exists(current_directory):
                    os.makedirs(current_directory)
                print_title(point.text)

            if point.name == 'p':
                link = point.find('a')
                if link is not None:
                    link = clean_pdf_link(link.attrs['href'])
                    ext = get_extension(link)
                    if not ext in forbidden_extensions:
                        print(shorten_title(point.text) + ' (' + link + ')')
                        try:
                            name = clean_text(point.text.split('[' + ext + ']')[0])
                            fullname = '.'.join((name, ext))
                            if not os.path.exists('/'.join((current_directory, fullname)) ):
                                download_file(link, current_directory, '.'.join((name, ext)))
                        except:
                            failures.append(point.text)
                        
        point = point.next_sibling          

    print('Done!')
    if failures:
        print('Some downloads have failed:')
        for fail in failures:
            print('> ' + fail)