import json
import os

import boto3
import cohere
import eml_parser
import openai
import pandas as pd
from typing import List
import re

from emlparse import get_eml_text

dev_boto_session = boto3.Session()
OPENAI_MAX_TOKENS = 200
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"

co = cohere.Client('kkLS4k4J8BOpYHaZcPEwbirzdS7w6TOpBfLQJKdp')


def get_secret(secret_name):
    client = dev_boto_session.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    secret = response["SecretString"]
    return json.loads(secret)

openai.api_key = get_secret("openai.com/cloud.admin@kognitos.com/api_key")["api_key"]


def get_gpt_response(
    messages: List,
    user: str = "koncierge",
    temperature: float = 0,
    max_tokens=800,
    model=DEFAULT_OPENAI_MODEL,
) -> str:
    print(f"Asking {model} for {messages}")
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        user=user,
    )
    result = response.choices[0]["message"]["content"].strip()
    return result


def get_invoice_details():
    res = []
    BASE_DIR = "./raw"
    for filename in os.listdir(BASE_DIR):
        if filename.endswith('.eml'):
            # filename = "FW_ Bank of America Payment_Remittance Advice.eml"
            body = get_eml_text(f"{BASE_DIR}/{filename}")
            body = re.sub('<!.*>', '', body.replace("\n", ""))
            prompt = (
                f"{body}\n"
                "Please provide an output which parses the above email with the following format and information you've extracted:"
                "|Invoice number or document reference number|invoice amount|\n"
                "|------------------------|-------------------|"
                # "What are the document reference numbers or invoice numbers in the above?\n"
                # "What are the corresponding invoice amounts in the above?"
            )

            #if False:
            #    # generate a prediction for a prompt
            #    prediction = co.generate(
            #        model='command-nightly',
            #        prompt=prompt,
            #        max_tokens=400,
            #        temperature=0.0,
            #    )

            try:
                result = get_gpt_response(
                    messages=[{"role": "user", "content": prompt}], user="koncierge"
                )
            except Exception as e:
                continue

            res.append(
                {
                    'filename': filename,
                    'dir': BASE_DIR,
                    'prompt': prompt,
                    # 'cohere': prediction.data[0].text,
                    'chat-gpt': result,
                }
            )

    return res


if __name__ == '__main__':
    res = get_invoice_details()

    new_response = {
        "Prompt": [],
        # "Cohere": [],
        "Chat-GPT": [],
        "filename": [],
    }

    for r in res:
        new_response["Prompt"].append(r['prompt'])
        # new_response["Cohere"].append(r['cohere'])
        new_response["Chat-GPT"].append(r['chat-gpt'])
        new_response["filename"].append(f"{r['dir']}/{r['filename']}")

    df = pd.DataFrame(new_response)
    file_path = 'invoice_data_summarize.xlsx'
    df.to_csv(file_path, index=False)
    #print(json.dumps(res, indent=4))
