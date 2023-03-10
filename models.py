import os
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, GPTNeoXForCausalLM, GPTNeoXTokenizerFast, \
    GPTNeoForCausalLM, GPT2Tokenizer, AutoModelForCausalLM
import openai

import utils

openai.api_key = os.getenv("OPENAI_API_KEY")



class GPT3:
    model = "text-davinci-003"
    seconds_per_query = (60 / 20) + 0.01
    @staticmethod
    def request_model(prompt):
        return openai.Completion.create(model=GPT3.model, prompt=prompt, max_tokens=250)

    @staticmethod
    def decode_response(response):
        return response["choices"][0]["text"]

    @staticmethod
    def query(prompt):
        return GPT3.decode_response(GPT3.request_model(prompt))


class HugginFaceModel:
    def query(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(utils.Parameters.devices[0])
        outputs = self.model.generate(**inputs, max_new_tokens=200)
        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

    def __call__(self, prompt):
        return self.query(prompt)


class T5(HugginFaceModel):
    def __init__(self, size="large"):
        self.model = AutoModelForSeq2SeqLM.from_pretrained(f"google/flan-t5-{size}").to(utils.Parameters.devices[0])
        self.tokenizer = AutoTokenizer.from_pretrained(f"google/flan-t5-{size}", model_max_length=600)


class T5XL(HugginFaceModel):
    def __init__(self, size="xxl"):
        assert size in ["xl", "xxl"]
        self.model = AutoModelForSeq2SeqLM.from_pretrained(f"google/flan-t5-{size}")
        self.tokenizer = AutoTokenizer.from_pretrained(f"google/flan-t5-{size}", model_max_length=600)
        device_map = {
            5: [0, 1, 2, 3, 4, 5, 6],
            6: [7, 8, 9, 10, 11, 12, 13, 14, 15],
            7: [16, 17, 18, 19, 20, 21, 22, 23]
        }
        self.model.parallelize(device_map)

    def query(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda:5")
        outputs = self.model.generate(**inputs, max_new_tokens=200)
        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]


class GPTNeoX(HugginFaceModel):
    def __init__(self):
        self.model = GPTNeoXForCausalLM.from_pretrained("EleutherAI/gpt-neox-20b").half().to(utils.Parameters.devices[0])
        self.tokenizer = GPTNeoXTokenizerFast.from_pretrained("EleutherAI/gpt-neox-20b")


class GPTNeo(HugginFaceModel):
    def __init__(self):
        self.model = GPTNeoForCausalLM.from_pretrained("EleutherAI/gpt-neo-1.3B").to(utils.Parameters.devices[0])
        self.tokenizer = GPT2Tokenizer.from_pretrained("EleutherAI/gpt-neo-1.3B")


class GPTJ(HugginFaceModel):
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B").to(utils.Parameters.devices[0])
        self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")

    def query(self, prompt):
        input_tokens = self.tokenizer(prompt, return_tensors="pt")
        input_ids = input_tokens.input_ids
        attention_mask = input_tokens.attention_mask
        outputs = self.model.generate(input_ids, attention_mask=attention_mask, do_sample=True, temperature=0.3,
                                      max_new_tokens=150)
        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0][len(prompt):]

    def __call__(self, prompt):
        return self.query(prompt)
