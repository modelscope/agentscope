# Chatroom Example

This example will show
- How to set up a chat room and use environment to share the chat history.
- How to generate a conversation between three agents.
- How to set up an auto reply assistant.


## Background

Here we demonstrate two types of chat room conversations with environment, one is self-organizing dialogue, and the other is automatic reply assistant.
For self-organizing conversations, after setting the agent persona for participating in the chat room, the model will automatically generate a reply based on the set agent persona and the history of chat room. Meanwhile, each agent can also reply to the corresponding agent based on the "@" symbol.
For the automatic reply assistant, if the user does not input text for a period of time, the model will automatically generate a reply based on the history of chat room.


## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
- `dashscope_chat` with `qwen-turbo`
- gpt-4o


## Prerequisites

- Install the lastest version of AgentScope by

```bash
git clone https://github.com/modelscope/agentscope
cd agentscope
pip install -e .\[distribute\]
```

- Prepare an OpenAI API key or Dashscope API key

## Running the Example

First fill your OpenAI API key or Dashscope API key in `chatroom_example.py` and `chatroom_with_assistant_example.py`, then execute these files to run the chatroom.
The following are the parameters required to run the script:

- `--use-dist`: Enable distributed mode.
- `--studio-url`: The url of agentscope studio.
- `--timeout`: Timeout for auto reply with assistant.

For example, if you want to start the simplest example for chatroom, you can use the following command

```bash
python chatroom_example.py
```

And if you want to run an example of `chatroom_with_assistant_example` in studio, you can use the following command.

```bash
python chatroom_with_assistant_example.py --studio-url "http://127.0.0.1:5000"
```

Here is an example output of `python chatroom_example.py`:

```
2024-08-22 15:35:45.140 | INFO     | agentscope.manager._model:load_model_configs:115 - Load configs for model wrapper: dash
2024-08-22 15:35:45.140 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
2024-08-22 15:35:45.140 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
2024-08-22 15:35:45.141 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
Carol: Starting our project planning session today! Let's discuss the key components for an engaging open-world game. Bob, could you share your thoughts on the game mechanics and systems?
Alice: Hey everyone! I've been thinking about the open world game we're working on. It would be great if we could gather some ideas for unique NPC behaviors that would add depth to our world. @Carol, do you have any specific scenarios or character types in mind that you think would fit well into our game environment?
2024-08-22 15:35:51.633 | INFO     | envs.chatroom:__call__:228 - Alice mentioned Carol.
Bob: Sure, for the game mechanics, I think incorporating dynamic weather systems and time of day changes could enhance player immersion. This way, NPC activities and environments adapt accordingly, creating a more realistic experience. @Alice, what kind of NPC behaviors were you envisioning? Could they interact differently based on the current weather or time of day?
2024-08-22 15:35:54.194 | INFO     | envs.chatroom:__call__:228 - Bob mentioned Alice.
Carol: Absolutely, integrating dynamic NPC behaviors based on the environment and time of day sounds intriguing. For example, we could have traders setting up their stalls only during certain hours, or farmers tending to their crops in daylight but resting under the stars. @Bob, how do you think we could implement these mechanics to ensure they don't feel too repetitive for players over time?
2024-08-22 15:36:02.657 | INFO     | envs.chatroom:__call__:228 - Carol mentioned Bob.
Alice: Absolutely, I was thinking along those lines as well. For example, fishermen might have better luck during certain times of day or under specific weather conditions. Farmers could have urgent tasks depending on the season or weather forecasts. And maybe traders would have special items to sell or deals to offer at night or during festivals. What do you think, @Bob?
2024-08-22 15:36:03.409 | INFO     | envs.chatroom:__call__:228 - Alice mentioned Bob.
Bob: I think those ideas are fantastic! To avoid repetition, we could introduce random events or quests that trigger based on the time of day or weather conditions. This would keep the gameplay fresh and engaging. Additionally, NPC preferences could change seasonally, adding another layer of complexity. For instance, a fisherman might prefer fishing during high tide, which could vary by season. I believe these dynamic elements will significantly enrich the player's experience. Let's brainstorm some specific examples and scenarios to flesh out these ideas further.
Carol: Great suggestions, everyone! Let's start documenting these ideas and create a detailed list. We'll also need to consider how these mechanics impact the game's overall narrative and pacing. Once we have a solid foundation, we can move on to designing the visual aspects and user interface. @Alice, can you give us some preliminary thoughts on how we might visually represent these dynamic changes in the game world?
2024-08-22 15:36:14.411 | INFO     | envs.chatroom:__call__:228 - Carol mentioned Alice.
Alice: Great suggestion, @Bob! I agree that introducing seasonal changes and random events will make the game world more alive and interesting. Let's consider having a festival once a month where NPCs participate in unique activities, like a harvest festival in autumn or a winter market with special winter-only goods. We could also have natural disasters like storms or wildfires that affect the environment and NPC behavior, forcing players to adapt their strategies. What do you think about incorporating such unpredictable elements into our game design?
2024-08-22 15:36:15.903 | INFO     | envs.chatroom:__call__:228 - Alice mentioned Bob.
Bob: Those are excellent ideas, @Alice! The festivals and natural disasters sound like they could really bring the world to life and challenge players in different ways. I'm particularly intrigued by the concept of festivals. Let's explore how we can integrate these events seamlessly into the game world and ensure they're both fun and immersive. @Carol, could you help us think about how these events might impact the overall narrative and quest progression?
2024-08-22 15:36:18.267 | INFO     | envs.chatroom:__call__:228 - Bob mentioned Alice.
2024-08-22 15:36:18.268 | INFO     | envs.chatroom:__call__:228 - Bob mentioned Carol.
Carol: Absolutely, integrating festivals and natural disasters will definitely add depth to the game world and provide unique challenges for players. These events can serve as pivotal points in the narrative, influencing storylines and quest objectives. For instance, a festival might require players to help prepare or manage specific aspects of the event, while a natural disaster could lead to emergent quests that involve rescue operations or rebuilding efforts. Let's outline how these events can be woven into the main storyline and side quests to maintain engagement throughout the game.
Alice: Absolutely, @Bob! Festivals and natural disasters can definitely add a lot of depth and excitement to the game. I think it's important to balance these elements so they don't overwhelm the player or disrupt the flow of the game too much. We should aim to make them integral parts of the story and questlines. For example, a festival could lead to a special quest where players help organize events or solve puzzles related to the festival. As for natural disasters, they could serve as obstacles that players must overcome, either by preparing for them or by finding creative solutions when they occur unexpectedly. Let's discuss how we can integrate these elements into our game design in a way that enhances the overall player experience.
2024-08-22 15:36:28.846 | INFO     | envs.chatroom:__call__:228 - Alice mentioned Bob.
Bob: I think this plan is shaping up beautifully. Let's focus on creating detailed mechanics for festivals and disasters, ensuring they not only add to the gameplay but also enhance the storytelling. We can then move on to refining the NPC behaviors and integrating them with the environmental changes. @Carol, @Alice, let's schedule a meeting to go over these concepts in detail and start fleshing out the designs. Goodbye for now, everyone. Let's make sure to touch base soon with updates on our progress.
2024-08-22 15:36:30.553 | INFO     | envs.chatroom:__call__:228 - Bob mentioned Alice.
2024-08-22 15:36:30.554 | INFO     | envs.chatroom:__call__:228 - Bob mentioned Carol.
Carol: Great summary, Bob! Your plan aligns perfectly with our goals for enhancing player immersion and narrative depth. Let's indeed focus on festivals and disasters as key elements that will drive our game's dynamics. Scheduling that meeting sounds like a good idea to delve deeper into these concepts. I'll coordinate the details and send out a calendar invite shortly. Looking forward to our next steps and seeing how we can refine NPC behaviors and environmental interactions. Keep up the great work, everyone! Goodbye for now, and let's stay in touch for updates.
Alice: Great summary, Bob! I'm excited to dive deeper into these mechanics and NPC behaviors. Let's ensure we capture the essence of each festival and disaster, making them unique and memorable. Looking forward to the meeting and seeing everyone's ideas come to life. Goodbye for now!
```

Another example output of `python chatroom_with_assistant_example.py`:

```
Alice: Hi Bob, nice to meet you. Can you tell me a bit about yourself?
2024-08-22 15:43:21.982 | INFO     | agentscope.manager._model:load_model_configs:115 - Load configs for model wrapper: dash
2024-08-22 15:43:21.982 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
2024-08-22 15:43:21.982 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
Bob: Of course, nice to meet you too, Alice. I'm originally from Hunan, a beautiful province in southern China known for its spicy food and stunning natural scenery.
Alice: Oh, that sounds fascinating! So, what do you do for a living, Bob?
Bob: I work as a software engineer. I've been in this field for about 5 years now, designing and developing various applications and systems. It's a challenging but rewarding job that keeps me on my toes.
Alice: That's great! It takes a lot of skill and creativity to be a good software engineer. Speaking of creativity, do you have any hobbies or activities you enjoy outside of work?
Bob: Yes, I'm quite passionate about playing board games. There's something really enjoyable about the strategy, competition, and social interaction they provide. Whether it's classic games like chess or more modern ones like Settlers of Catan, I find them all very engaging.
Alice: Board games are a wonderful way to unwind and connect with friends and family. It sounds like you have a great balance between your professional and personal life, Bob. Thanks for sharing!
Bob: Absolutely, thank you for asking, Alice. It was a pleasure chatting with you.
2024-08-22 15:43:21.985 | INFO     | agentscope.models.model:__init__:203 - Initialize model by configuration [dash]
Carol: Hello Bob, thank you for joining us today. To start off, could you tell me where you're from?
User input:
Bob: [auto reply] Sure, Carol. I'm from Hunan, a province in southern China famous for its spicy cuisine and breathtaking landscapes.
Carol: That's interesting! Thank you, Bob. Now, could you share which school you graduated from?
User input:
Bob: [auto reply] Sorry, but I can't answer that question based on our previous chat.
Carol: OK, Bob. What about your profession? Could you tell me more about that?
User input:
Bob: [auto reply] I work as a software engineer. My role involves designing and developing various applications and systems. I've been doing this for around 5 years now.
User input:
Carol: That sounds like an exciting career path. Lastly, could you share some of your hobbies with us?

Bob: [auto reply] Sure, I enjoy playing board games in my free time. They offer a great mix of strategy, competition, and social interaction. From classic games like chess to modern ones like Settlers of Catan, I find them all very engaging.
User input:
Carol: Thank you, Bob, for sharing these details with us. It was great having you on the show. Have a fantastic day!

Goodbye

Bob: [auto reply] Goodbye! It was nice chatting with you. Have a great day!
```