"""
EP05: Process Inputs — Chain of Thought Reasoning
==================================================
使用 Chain-of-Thought 提示让模型逐步推理，并用 Inner Monologue 隐藏中间步骤。
"""
from config import get_completion_from_messages


DELIMITER = "####"

SYSTEM_MESSAGE = f"""
Follow these steps to answer the customer queries.
The customer query will be delimited with four hashtags,\
i.e. {DELIMITER}.

Step 1:{DELIMITER} First decide whether the user is \
asking a question about a specific product or products. \
Product category doesn't count.

Step 2:{DELIMITER} If the user is asking about \
specific products, identify whether \
the products are in the following list.
All available products:
1. Product: TechPro Ultrabook
   Category: Computers and Laptops
   Brand: TechPro
   Model Number: TP-UB100
   Warranty: 1 year
   Rating: 4.5
   Features: 13.3-inch display, 8GB RAM, 256GB SSD, Intel Core i5 processor
   Description: A sleek and lightweight ultrabook for everyday use.
   Price: $799.99

2. Product: BlueWave Gaming Laptop
   Category: Computers and Laptops
   Brand: BlueWave
   Model Number: BW-GL200
   Warranty: 2 years
   Rating: 4.7
   Features: 15.6-inch display, 16GB RAM, 512GB SSD, NVIDIA GeForce RTX 3060
   Description: A high-performance gaming laptop for an immersive experience.
   Price: $1199.99

3. Product: PowerLite Convertible
   Category: Computers and Laptops
   Brand: PowerLite
   Model Number: PL-CV300
   Warranty: 1 year
   Rating: 4.3
   Features: 14-inch touchscreen, 8GB RAM, 256GB SSD, 360-degree hinge
   Description: A versatile convertible laptop with a responsive touchscreen.
   Price: $699.99

4. Product: TechPro Desktop
   Category: Computers and Laptops
   Brand: TechPro
   Model Number: TP-DT500
   Warranty: 1 year
   Rating: 4.4
   Features: Intel Core i7 processor, 16GB RAM, 1TB HDD, NVIDIA GeForce GTX 1660
   Description: A powerful desktop computer for work and play.
   Price: $999.99

5. Product: BlueWave Chromebook
   Category: Computers and Laptops
   Brand: BlueWave
   Model Number: BW-CB100
   Warranty: 1 year
   Rating: 4.1
   Features: 11.6-inch display, 4GB RAM, 32GB eMMC, Chrome OS
   Description: A compact and affordable Chromebook for everyday tasks.
   Price: $249.99

Step 3:{DELIMITER} If the message contains products \
in the list above, list any assumptions that the \
user is making in their \
message e.g. that Laptop X is bigger than \
Laptop Y, or that Laptop Z has a 2 year warranty.

Step 4:{DELIMITER}: If the user made any assumptions, \
figure out whether the assumption is true based on your \
product information.

Step 5:{DELIMITER}: First, politely correct the \
customer's incorrect assumptions if applicable. \
Only mention or reference products in the list of \
5 available products, as these are the only 5 \
products that the store sells. \
Answer the customer in a friendly tone.

Use the following format:
Step 1:{DELIMITER} <step 1 reasoning>
Step 2:{DELIMITER} <step 2 reasoning>
Step 3:{DELIMITER} <step 3 reasoning>
Step 4:{DELIMITER} <step 4 reasoning>
Response to user:{DELIMITER} <response to customer>

Make sure to include {DELIMITER} to separate every step.
"""


def demo_chain_of_thought():
    print("=" * 60)
    print("Demo 1: Chain-of-Thought — 产品价格对比")
    print("=" * 60)

    user_message = "by how much is the BlueWave Chromebook more expensive than the TechPro Desktop"
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": f"{DELIMITER}{user_message}{DELIMITER}"},
    ]
    response = get_completion_from_messages(messages)
    print(f"[完整推理过程]\n{response}\n")


def demo_non_product_query():
    print("=" * 60)
    print("Demo 2: 非产品问题处理")
    print("=" * 60)

    user_message = "do you sell tvs"
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": f"{DELIMITER}{user_message}{DELIMITER}"},
    ]
    response = get_completion_from_messages(messages)
    print(f"[完整推理过程]\n{response}\n")

    # Inner Monologue: 只显示最终回复
    try:
        final_response = response.split(DELIMITER)[-1].strip()
    except Exception:
        final_response = "Sorry, I'm having trouble right now, please try asking another question."
    print(f"[Inner Monologue — 仅最终回复]\n{final_response}\n")


if __name__ == "__main__":
    demo_chain_of_thought()
    demo_non_product_query()
    print("✅ EP05 完成！")
