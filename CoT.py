import sys
import openai
import random
import time, os

with open("key.txt", 'r', encoding='utf-8') as f:
    keys = [i.strip() for i in f.readlines()]

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
    for i in range(1, 57):
        try:
            os.makedirs('CoT_outputs/res'+str(i))
        except:
            pass

    for i in range(1, 57):
        with open('CoT_outputs/res'+str(i)+'/story.txt', 'a+', encoding='utf-8') as f2:
            f2.seek(0)
            num = len(f2.readlines())
            print('res'+str(i)+'已有'+str(num)+'个故事')
            if num >= 9: #9个prompt指令都执行了，读取下一个res文件的prompt
                continue
            else:
                with open('outputs/res'+str(i)+'/prompt.txt') as f:
                    fli = f.readlines()
                    for prompt in fli[num:]:  # 从第num+1个指令开始
                        prompt1 = prompt + '\nAfter you write the story, point out the unclarities in the story in an organized list.' \
                                           'Then provide further details to address the unclarities for' + str(3) + 'rounds. ' \
                                           'At last, integrate the details into the original story and start with the identifier "Integrated Story". '
                        messages = [
                            {"role": "user", "content": prompt1}
                        ]
                        f3 = open('CoT_outputs/res'+str(i)+'/whole_output.txt', 'a+', encoding='utf-8')
                        generate(messages, f2, f3)
                        f2.flush() #直接将缓冲区内容写在文件中
                        f3.close()

                        print("故事" + str(fli.index(prompt) + 1) + "撰写完成")