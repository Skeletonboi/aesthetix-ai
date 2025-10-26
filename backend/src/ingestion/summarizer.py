from openai import OpenAI
import json
from yt_transcript_util.utils import save_vids_dic, load_vids_dic
from src.config import Config

class TranscriptProcessor():
    def __init__(self, vids_dic=None, transcript_savepath=None):
        if vids_dic:
            self.vids_dic = vids_dic
        elif transcript_savepath:
            with open(transcript_savepath, 'r') as file:
                self.vids_dic = json.load(file)
        else:
            raise Exception('No transcript dictionary or savepath provided')

    def remove_empty(self, vids_dic=None, threshold=100):
        """
        Filters out videos with vid_ids
        """
        if not vids_dic:
            vids_dic = self.vids_dic
        
        empty_vids = []
        for vid_id in vids_dic.keys():
            if len(vids_dic[vid_id]['transcript']) <= threshold:
                print(f"Video ID {vid_id}has empty or near-empty transcript")
                empty_vids.append(vid_id)

        for vid_id in empty_vids:
            vids_dic.pop(vid_id)
            
        return vids_dic, empty_vids
    
class TranscriptSummarizer(TranscriptProcessor):
    def __init__(self, vids_dic=None, transcript_savepath=None):
        super().__init__(vids_dic=vids_dic, transcript_savepath=transcript_savepath)
        self.default_model_name = 'gpt-5-mini'
        self.default_dev_prompt = \
            """
            As a fitness-science based transcript data extractor and summarizer, break down and summarize the key fitness advice provided 
            in the following transcript into anonymized bullet points, each containing a key takeaway, conclusion, or principle pertaining 
            to fitness. All outputs must be completely anonymized from the author, each bullet point should contain only the factual and/or 
            advisory content ONLY - ignore irrelevant stories, promotions, and yapping. 
            If no relevant/applicable fitness advice can be derived from the transcript, return an empty string.
            Include all research sources, as well as reasoning traces, stated or suggested facts pertaining to the fitness advice.
            Use only material from the provided transcript, do not include your own opinions.
            """
    
    def summarize_ts(self, ts, model_name=None, dev_prompt=None):
        if not dev_prompt:
            dev_prompt = self.default_dev_prompt
        if not model_name:
            model_name = self.default_model_name

        try:
            client = OpenAI(api_key=Config.LLM_API_KEY)
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {'role': 'developer', 'content': dev_prompt},
                    {'role': 'user', 'content': ts}
                ]
            )
        except Exception as e:
            print(f'Failed to summarize transcript: {e}')
            raise e

        return completion.choices[0].message.content

    def summarize_transcripts(self, summary_savepath, vids_dic=None, model_name=None, dev_prompt=None):
        if not vids_dic:
            vids_dic = self.vids_dic

        # Load existing summaries
        file_vids_dic = load_vids_dic(summary_savepath)
        
        n_vids_since_last_save = 0
        n = len(vids_dic.keys())
        failed_vids = []
        for i, vid_id in enumerate(vids_dic.keys()):
            # if vid_id in file_vids_dic:
            if vid_id in file_vids_dic and 'summary' in file_vids_dic[vid_id] and file_vids_dic[vid_id]['summary']:
                continue
            if i % 10 == 0 and n_vids_since_last_save > 0:
                save_vids_dic(file_vids_dic, summary_savepath)
                n_vids_since_last_save = 0
            print(f'Summarizing video {i + 1}/{n}, Video ID: {vid_id}')
            try:
                output = self.summarize_ts(ts=vids_dic[vid_id]['transcript'], model_name=model_name, dev_prompt=dev_prompt)
            except:
                failed_vids.append(vid_id)
                continue

            file_vids_dic[vid_id] = vids_dic[vid_id].copy()
            file_vids_dic[vid_id]['summary'] = output
            n_vids_since_last_save += 1
        
        save_vids_dic(file_vids_dic, summary_savepath)

        return file_vids_dic, failed_vids

