import os
from openai import OpenAI

def main():
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ.get("NVIDIA_API_KEY")
    )

    model_id = "z-ai/glm5" # "moonshotai/kimi-k2.5"
    
    print(f"Sending request to {model_id}...")

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "user", "content": "My car is dirty. I need to wash it. The car wash is  50 meters away. Should I walk or drive?"}
        ],
        temperature=1.0,  # Recommended temperature for thinking mode
        max_tokens=4096,  # Must be large enough to accommodate the reasoning trace
        stream=False,
        extra_body={"chat_template_kwargs":{"enable_thinking":True,"clear_thinking":False}},
    )

    message = response.choices[0].message

    # 1. Extract the Thinking Process (Reasoning Trace)
    reasoning = getattr(message, 'reasoning_content', None) 

    # 2. Extract the Final Answer
    final_answer = message.content

    print("\n====== THINKING PROCESS ======")
    print(reasoning if reasoning else "(No reasoning trace returned)")
    
    print("\n====== FINAL ANSWER ======")
    print(final_answer)

if __name__ == "__main__":
    main()