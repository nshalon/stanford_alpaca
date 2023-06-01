import email
from bs4 import BeautifulSoup, NavigableString
from prettytable import PrettyTable

def get_eml_text(filepath):
    body = ""
    # Read the .eml file
    with open(filepath, 'r') as f:
        msg = email.message_from_string(f.read())

    # Get the email body
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                body = part.get_payload(decode=True)
                break
    else:
        body = msg.get_payload(decode=True)

    if not body:
        return ""
    # Parse the email body using BeautifulSoup
    soup = BeautifulSoup(body, 'html.parser')

    # Function to convert HTML table to PrettyTable (ASCII table)
    def html_to_ascii_table(html_table):
        ascii_table = PrettyTable()
        headers = [th.text.strip() for th in html_table.find_all('th')]
        ascii_table.field_names = headers

        ascii_rows = list()
        for row in html_table.find_all('tr'):
            ascii_rows.append([td.text.strip() for td in row.find_all('td')])
            
        if not headers:
            # Find the max length row.
            num_cols = max(len(r) for r in ascii_rows)
        else:
            num_cols = len(headers)
            
        for row in ascii_rows:
            ascii_table.add_row(row + ['']*(num_cols - len(row)))

        return ascii_table

    # Function to extract text and replace tables with ASCII tables
    def extract_text_and_tables(element):
        result = ''
        for child in element.children:
            if isinstance(child, NavigableString):
                if "NavigableString" in str(type(child)):
                    result += str(child)
            elif child.name == 'table':
                ascii_table = html_to_ascii_table(child)
                result += '\n' + str(ascii_table) + '\n'
                # result += extract_text_and_tables(child)
            else:
                result += extract_text_and_tables(child)
        return result

    # Get the text content of the email body with tables replaced
    email_text = extract_text_and_tables(soup)
    return email_text

    # Print the email text
    #print(email_text)


