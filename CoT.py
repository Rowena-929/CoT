import sys
import openai
import random
import time, os
from llm4story import *

with open("key.txt", 'r', encoding='utf-8') as f:
    keys = [i.strip() for i in f.readlines()]

plot_kind = []
subject = ['lovers', 'cats', 'survivors']
genre = ['Historical Fiction', 'Literary Fiction', 'Science Fiction']
mood = ['angry']
# num_kind = len(suject) * len(mood) * len(genre)

with open("inputs/plot.txt", 'r', encoding='utf-8') as file:  # yyx change
    reddit_plot = [k.strip() for k in file.readlines()]
    for i in range(len(reddit_plot)):
        j = reddit_plot[i].find('[ ')
        if j != -1:  # kind:[_IP/WP/FF/EU/CW/RF/OT/PI/Wp/PM_]_
            plot_kind.append(reddit_plot[i][j + 2:j + 4])
            reddit_plot[i] = reddit_plot[i][0:j].strip() + reddit_plot[i][j + 6:].strip()
        else:
            plot_kind.append('')

with open('../data/movie_data.json', 'r') as fi:
    movie_data = json.load(fi)

def generate_prompt(plot_num): #生成prompt
    request = []
    prompts = []
    for count in range(len(suject) * len(mood) * len(genre)):
        request.append({'plots': [reddit_plot[plot_num]]})
    count = 0
    for a in mood:  # 'mood': [], 'genre': [], 'subjects': [],
        for b in genre:
            for c in subject:
                request[count]['mood'] = a
                request[count]['genre'] = [b]
                request[count]['subjects'] = [c]
                count += 1

    for queries in request:
        all_recommendations = get_all_recommend(movie_data, queries, 4)
        example_id = get_best_example(all_recommendations)
        example = movie_data[example_id]
        examples = [example]
        prompt = make_prompt(examples=examples, conditions=queries)
        prompt1 = prompt + '\nAfter you write the story, point out the unclarities in the story in an organized list.' \
                           'Then provide further details to address the unclarities for' + str(3) + 'rounds. ' \
                           'At last, integrate the details into the original story and start with the identifier "Integrated Story". '
        with open('CoT_outputs/res' + str(plot_num + 1) + '/prompt.txt', 'a+', encoding='utf-8') as f:
            f.write(prompt1.replace('\n', ''))
            f.write('\n')
        prompts.append(prompt1.replace('\n', ''))

    return prompts

def generate(messages, f2, f3):
    try:
        start = time.time()
        index_num = random.randint(0, len(keys)-1)
        openai.api_key = keys[index_num] # 每次调用使用不同的key防止被ban

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        generation = response['choices'][0]['message']['content'].replace('\n\n', '\n')
        #print(generation)
        if generation.find("I'm sorry") != -1 or generation.find("an AI language model") != -1: #拒绝该请求
            #print(generation)
            f2.write('gpt refused to fulfill this prompt\n')
            f3.write(generation)
            f3.write('\n-----------------------------------------------\n')
            print("用时：{:.2f}s".format(time.time() - start), end=' ')
            return
        index = generation.index("Integrated Story") + 17  #加17去掉"Integrated Story"字符，只留下故事
        story = generation[index:].replace('\n', '')
        # if story.find("Unclarities:") == -1:
        #     generate(messages)      #gpt错误生成integrated story再生成unclarities
        f3.write(generation)
        f3.write('\n-----------------------------------------------\n')
        f2.write(story)
        f2.write('\n')
        print("用时：{:.2f}s".format(time.time() - start), end=' ')

    except openai.error.RateLimitError as e1:
        # print(str(e))
        if 'You exceeded your current quota' in str(e1):
            delete = open("exceeded_keys.txt", 'a+', encoding='utf-8')
            delete.write(openai.api_key + '\n')
            delete.close()
            if str(openai.api_key) in keys:
                keys.remove(str(openai.api_key))
        elif 'Limit: 3 / min. Please try again in 20s' in str(e1):
            time.sleep(40)  # 根据报错信息，出错时自动等40秒后继续发送任务
        generate(messages, f2, f3) #处理完错误后重开
    except openai.error.APIError as e2:
        if 'The server had an error while processing your request. Sorry about that!' in str(e2):
            time.sleep(10)
            generate(messages, f2, f3)
        elif 'Error communicating with OpenAI' in str(e2):
            print('网络错误，请检查网络连接')
            sys.exit()
    except ValueError as e2:
        generate(messages, f2, f3)



if __name__=='__main__':
    for i in range(1, 51):
        try:
            os.makedirs('CoT_outputs/res'+str(i))
        except:
            pass

    for i in range(1, 51):
        if not os.path.exists('CoT_outputs/res'+str(i)+'/prompt.txt'):
            prompts = generate_prompt(i - 1) #先生成所有prompts
        else:
            with open('CoT_outputs/res'+str(i)+'/prompt.txt') as f:
                prompts = f.readlines()
        with open('CoT_outputs/res'+str(i)+'/story.txt', 'a+', encoding='utf-8') as f2:
            f2.seek(0)
            num = len(f2.readlines())
            print('res'+str(i)+'已有'+str(num)+'个故事')
            if num >= 9: #这个plot的所有故事已生成完
                continue
            else:
                for prompt in prompts[num:]:  # 从第num+1个指令开始
                    messages = [
                        {"role": "user", "content": prompt}
                    ]
                    f3 = open('CoT_outputs/res'+str(i)+'/whole_output.txt', 'a+', encoding='utf-8')
                    generate(messages, f2, f3)
                    f2.flush() #直接将缓冲区内容写在文件中
                    f3.close()
                    print("plot" + str(i) + "故事" + str(num + 1) + "撰写完成")
                    num += 1
