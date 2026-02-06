"""
Seed data for FinSakhi Learning Modules & Lessons
4 Pillars × 3 Levels = 12 Modules, each with 2-3 lessons
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal, Module, Lesson, init_db

def seed():
    init_db()
    db = SessionLocal()

    # Clear existing
    db.query(Lesson).delete()
    db.query(Module).delete()
    db.commit()

    modules_data = [
        # ============================
        # BEGINNER — SAVINGS
        # ============================
        {
            "pillar": "savings", "level": "beginner",
            "title_en": "Why Save Money?", "title_hi": "पैसे क्यों बचाएं?",
            "description_en": "Learn why keeping money safe matters", "description_hi": "जानें पैसे सुरक्षित रखना क्यों ज़रूरी है",
            "order_index": 1,
            "lessons": [
                {
                    "title_en": "Ramesh's Story — Saving Starts Small",
                    "title_hi": "रमेश की कहानी — बचत छोटी शुरू होती है",
                    "story_en": "Meet Ramesh. Every day, he earns some money. Earlier, he kept it at home. Sometimes it got lost. Sometimes it got spent without planning. One day, Ramesh opened a bank account. Now his money is safe. It also grows slowly through interest. Saving means keeping money safe for tomorrow.",
                    "story_hi": "रमेश से मिलिए। वह रोज़ कुछ पैसे कमाता है। पहले वह घर पर रखता था। कभी खो जाते, कभी बिना सोचे खर्च हो जाते। एक दिन रमेश ने बैंक खाता खोला। अब उसका पैसा सुरक्षित है और ब्याज से बढ़ भी रहा है।",
                    "takeaway_en": "Even ₹10 saved daily = ₹3,650 in a year. Start small, stay consistent.",
                    "takeaway_hi": "रोज़ ₹10 भी बचाएं = साल में ₹3,650। छोटी शुरुआत करें, लगातार रहें।",
                    "scenario_en": json.dumps({"question": "Ramesh gets ₹500 today. What should he do?", "options": [{"text": "Spend it all on shopping", "correct": False}, {"text": "Save some in the bank and spend the rest wisely", "correct": True}, {"text": "Give it to an unknown person who promises to double it", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "रमेश को आज ₹500 मिले। उसे क्या करना चाहिए?", "options": [{"text": "सब खरीदारी में खर्च कर दे", "correct": False}, {"text": "कुछ बैंक में बचाए और बाकी समझदारी से खर्च करे", "correct": True}, {"text": "किसी अनजान को दे दे जो दोगुना करने का वादा करे", "correct": False}]}),
                    "tool_suggestion": "savings_goal", "xp_reward": 10, "order_index": 1
                },
                {
                    "title_en": "Home vs Bank — Where is Money Safer?",
                    "title_hi": "घर vs बैंक — पैसा कहाँ सुरक्षित?",
                    "story_en": "Geeta keeps ₹5,000 at home in a box. One rainy day, water leaks in and the notes get damaged. Her neighbour Priya has the same ₹5,000 in a savings account. After one year, Priya's money grew to ₹5,200 because of interest. Geeta's money is still ₹5,000 — or less. Banks protect your money AND help it grow.",
                    "story_hi": "गीता ₹5,000 घर में डिब्बे में रखती है। एक बारिश के दिन पानी लग गया और नोट खराब हो गए। उसकी पड़ोसन प्रिया ने वही ₹5,000 बचत खाते में रखे थे। एक साल बाद प्रिया के पैसे ₹5,200 हो गए। बैंक पैसे सुरक्षित रखता है और बढ़ाता भी है।",
                    "takeaway_en": "A savings account is free, safe, and earns interest. Open one today.",
                    "takeaway_hi": "बचत खाता मुफ्त है, सुरक्षित है, और ब्याज भी मिलता है।",
                    "scenario_en": json.dumps({"question": "You have ₹2,000 savings. Where should you keep it?", "options": [{"text": "Under the mattress", "correct": False}, {"text": "In a savings account at the bank", "correct": True}, {"text": "Lend it to a friend", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "आपके पास ₹2,000 बचत है। कहाँ रखें?", "options": [{"text": "गद्दे के नीचे", "correct": False}, {"text": "बैंक के बचत खाते में", "correct": True}, {"text": "दोस्त को उधार दे दें", "correct": False}]}),
                    "tool_suggestion": "savings_goal", "xp_reward": 10, "order_index": 2
                }
            ]
        },
        # ============================
        # BEGINNER — CREDIT
        # ============================
        {
            "pillar": "credit", "level": "beginner",
            "title_en": "Borrowing Safely", "title_hi": "सुरक्षित उधार",
            "description_en": "Learn the difference between safe and unsafe borrowing", "description_hi": "सुरक्षित और असुरक्षित उधार का फर्क समझें",
            "order_index": 2,
            "lessons": [
                {
                    "title_en": "Sita's Choice — Bank vs Moneylender",
                    "title_hi": "सीता का फैसला — बैंक या साहूकार",
                    "story_en": "Sita needs ₹10,000 for her daughter's education. She has two options. One is a money lender who charges 5% per month. Second is a bank loan at 12% per year. Money lenders ask much more money back. Banks ask less and give time to repay through EMI. Borrowing from bank is safer and cheaper.",
                    "story_hi": "सीता को बेटी की पढ़ाई के लिए ₹10,000 चाहिए। एक विकल्प है साहूकार जो 5% महीना लेता है। दूसरा है बैंक लोन 12% साल। साहूकार ज़्यादा वसूलता है। बैंक कम लेता है और EMI में समय देता है। बैंक से उधार सुरक्षित है।",
                    "takeaway_en": "Always compare interest rates. Banks are cheaper than moneylenders.",
                    "takeaway_hi": "हमेशा ब्याज दर तुलना करें। बैंक साहूकार से सस्ता है।",
                    "scenario_en": json.dumps({"question": "You need ₹10,000 urgently. What should you do?", "options": [{"text": "Borrow from a moneylender at high interest", "correct": False}, {"text": "Take a bank loan with fixed EMI", "correct": True}, {"text": "Borrow from multiple people and worry later", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "आपको ₹10,000 की तुरंत ज़रूरत है। क्या करें?", "options": [{"text": "साहूकार से ऊंची ब्याज पर लें", "correct": False}, {"text": "बैंक से EMI वाला लोन लें", "correct": True}, {"text": "कई लोगों से उधार लें और बाद में सोचें", "correct": False}]}),
                    "tool_suggestion": "emi_calculator", "xp_reward": 10, "order_index": 1
                },
                {
                    "title_en": "What is Interest? — Simple Explanation",
                    "title_hi": "ब्याज क्या है? — आसान समझ",
                    "story_en": "When you borrow money, you pay extra to the lender. This extra is called interest. If you borrow ₹1,000 at 10% per year, after one year you return ₹1,100. The ₹100 extra is the interest. Lower interest = less burden on you. Always ask 'What is the interest rate?' before borrowing.",
                    "story_hi": "जब आप पैसे उधार लेते हैं, तो अतिरिक्त देना पड़ता है। इसे ब्याज कहते हैं। ₹1,000 पर 10% सालाना ब्याज = एक साल बाद ₹1,100 लौटाना। ₹100 अतिरिक्त ब्याज है। कम ब्याज = कम बोझ। हमेशा पूछें 'ब्याज दर क्या है?'",
                    "takeaway_en": "Interest is the cost of borrowing. Lower is better. Always ask before you borrow.",
                    "takeaway_hi": "ब्याज उधार की कीमत है। कम बेहतर। उधार लेने से पहले हमेशा पूछें।",
                    "scenario_en": json.dumps({"question": "Two loans available: Bank at 12%/year or moneylender at 3%/month. Which is cheaper?", "options": [{"text": "Moneylender — 3% sounds less", "correct": False}, {"text": "Bank — 12%/year is cheaper than 36%/year", "correct": True}, {"text": "Both are the same", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "दो लोन उपलब्ध: बैंक 12%/साल या साहूकार 3%/महीना। कौन सस्ता?", "options": [{"text": "साहूकार — 3% कम लगता है", "correct": False}, {"text": "बैंक — 12%/साल सस्ता है बनाम 36%/साल", "correct": True}, {"text": "दोनों एक जैसे हैं", "correct": False}]}),
                    "tool_suggestion": "emi_calculator", "xp_reward": 10, "order_index": 2
                }
            ]
        },
        # ============================
        # BEGINNER — INVESTMENTS
        # ============================
        {
            "pillar": "investments", "level": "beginner",
            "title_en": "Making Money Grow", "title_hi": "पैसे को बढ़ाना",
            "description_en": "Understand the difference between saving and investing", "description_hi": "बचत और निवेश का फर्क समझें",
            "order_index": 3,
            "lessons": [
                {
                    "title_en": "Saving vs Investing — What's the Difference?",
                    "title_hi": "बचत vs निवेश — क्या फर्क है?",
                    "story_en": "Saving keeps money safe. Investing helps money grow. A Fixed Deposit is like locking money safely in a box that gives you extra money. No risk, no tension. If someone says 'double your money in 1 month' — it is FAKE. Real investments grow slowly but surely.",
                    "story_hi": "बचत पैसे सुरक्षित रखती है। निवेश पैसे बढ़ाता है। FD एक सुरक्षित डिब्बे जैसी है जो अतिरिक्त पैसे देती है। कोई जोखिम नहीं। अगर कोई कहे '1 महीने में पैसा दोगुना' — यह धोखा है।",
                    "takeaway_en": "Start with FD or RD. Avoid 'get rich quick' schemes — they are scams.",
                    "takeaway_hi": "FD या RD से शुरू करें। 'जल्दी अमीर बनो' योजनाओं से बचें — वे धोखा हैं।",
                    "scenario_en": json.dumps({"question": "Someone offers to double your ₹5,000 in one month. What do you do?", "options": [{"text": "Give the money — sounds great!", "correct": False}, {"text": "Refuse — this is likely a scam", "correct": True}, {"text": "Give half and see what happens", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "कोई कहता है ₹5,000 एक महीने में दोगुना कर देगा। क्या करें?", "options": [{"text": "पैसे दे दो — अच्छा लगता है!", "correct": False}, {"text": "मना करो — यह शायद धोखा है", "correct": True}, {"text": "आधे दो और देखो क्या होता है", "correct": False}]}),
                    "tool_suggestion": None, "xp_reward": 10, "order_index": 1
                },
                {
                    "title_en": "Fixed Deposit — Your First Safe Investment",
                    "title_hi": "फिक्स्ड डिपॉजिट — आपका पहला सुरक्षित निवेश",
                    "story_en": "Mohan had ₹10,000 in savings. He put it in a Fixed Deposit for 1 year at 7% interest. After 1 year he got ₹10,700 without doing anything. FD is safe because the bank guarantees your money back plus interest. You just need to wait patiently.",
                    "story_hi": "मोहन के पास ₹10,000 बचत थे। उसने 7% ब्याज पर 1 साल की FD करवाई। 1 साल बाद उसे ₹10,700 मिले बिना कुछ किए। FD सुरक्षित है क्योंकि बैंक पैसे वापसी की गारंटी देता है।",
                    "takeaway_en": "FD gives guaranteed returns. Great for beginners. Start with any amount.",
                    "takeaway_hi": "FD गारंटीड रिटर्न देती है। शुरुआत के लिए बढ़िया।",
                    "scenario_en": json.dumps({"question": "You have ₹10,000 you won't need for a year. Best option?", "options": [{"text": "Keep at home", "correct": False}, {"text": "Put in a 1-year Fixed Deposit", "correct": True}, {"text": "Buy lottery tickets", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "₹10,000 हैं जो एक साल तक नहीं चाहिए। सबसे अच्छा?", "options": [{"text": "घर पर रखो", "correct": False}, {"text": "1 साल की FD में डालो", "correct": True}, {"text": "लॉटरी टिकट खरीदो", "correct": False}]}),
                    "tool_suggestion": None, "xp_reward": 10, "order_index": 2
                }
            ]
        },
        # ============================
        # BEGINNER — SMALL BUSINESS
        # ============================
        {
            "pillar": "small_business", "level": "beginner",
            "title_en": "Running a Small Business", "title_hi": "छोटा व्यापार चलाना",
            "description_en": "Learn basic business money management", "description_hi": "व्यापार के पैसों का प्रबंधन सीखें",
            "order_index": 4,
            "lessons": [
                {
                    "title_en": "Meena's Tea Stall — Separate Business Money",
                    "title_hi": "मीना की चाय की दुकान — व्यापार का पैसा अलग रखो",
                    "story_en": "Meena runs a small tea stall. Earlier, she mixed home money and business money. She never knew profit or loss. Now she keeps them separate. She writes how much she earns and spends each day. Her business is growing slowly but safely. Separate business and personal money — this is rule number one.",
                    "story_hi": "मीना चाय की दुकान चलाती है। पहले वह घर और दुकान का पैसा मिला देती थी। उसे कभी पता नहीं चलता था कि फायदा हुआ या नुकसान। अब वह अलग रखती है। रोज़ का हिसाब लिखती है। व्यापार धीरे-धीरे बढ़ रहा है। व्यापार और घर का पैसा अलग रखो — यह पहला नियम है।",
                    "takeaway_en": "Keep business money and personal money separate. Write daily income and expenses.",
                    "takeaway_hi": "व्यापार और घर का पैसा अलग रखें। रोज़ आय-खर्च लिखें।",
                    "scenario_en": json.dumps({"question": "You earn ₹500 from your shop today. What should you do?", "options": [{"text": "Mix it with home expenses", "correct": False}, {"text": "Keep it separate and note it in a register", "correct": True}, {"text": "Spend it immediately on personal things", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "आज दुकान से ₹500 कमाए। क्या करें?", "options": [{"text": "घर के खर्चों में मिला दो", "correct": False}, {"text": "अलग रखो और रजिस्टर में लिखो", "correct": True}, {"text": "तुरंत अपनी चीज़ों पर खर्च करो", "correct": False}]}),
                    "tool_suggestion": "budget_tool", "xp_reward": 10, "order_index": 1
                }
            ]
        },
        # ============================
        # INTERMEDIATE — SAVINGS
        # ============================
        {
            "pillar": "savings", "level": "intermediate",
            "title_en": "Smart Saving Strategies", "title_hi": "स्मार्ट बचत रणनीतियाँ",
            "description_en": "Learn about emergency funds and budgeting", "description_hi": "आपातकालीन निधि और बजट सीखें",
            "order_index": 5,
            "lessons": [
                {
                    "title_en": "Emergency Fund — Your Safety Net",
                    "title_hi": "आपातकालीन निधि — आपका सुरक्षा जाल",
                    "story_en": "Raju's son got sick suddenly. Hospital bill was ₹15,000. Raju had no savings. He had to borrow from a moneylender at high interest. His neighbour Suresh also faced a similar situation. But Suresh had an emergency fund — 3 months of expenses saved in bank. He paid the hospital bill easily without any debt. An emergency fund is money you save ONLY for emergencies — health issues, job loss, or urgent repairs.",
                    "story_hi": "राजू का बेटा अचानक बीमार पड़ा। अस्पताल का बिल ₹15,000 आया। राजू की कोई बचत नहीं थी। उसे साहूकार से ऊंचे ब्याज पर उधार लेना पड़ा। उसके पड़ोसी सुरेश ने भी ऐसी ही स्थिति झेली। लेकिन सुरेश के पास 3 महीने का खर्चा बैंक में था। उसने आसानी से बिल चुकाया।",
                    "takeaway_en": "Save 3 months of expenses as emergency fund. Don't touch it for regular spending.",
                    "takeaway_hi": "3 महीने का खर्चा आपातकालीन निधि के रूप में बचाएं।",
                    "scenario_en": json.dumps({"question": "You saved ₹20,000 as emergency fund. A friend asks to borrow it for a wedding. What do you do?", "options": [{"text": "Give it — friendship is important", "correct": False}, {"text": "Politely refuse — emergency fund is only for emergencies", "correct": True}, {"text": "Give half", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "₹20,000 आपातकालीन निधि बचाई। दोस्त शादी के लिए माँगता है। क्या करें?", "options": [{"text": "दे दो — दोस्ती ज़रूरी है", "correct": False}, {"text": "विनम्रता से मना करो — यह सिर्फ इमरजेंसी के लिए है", "correct": True}, {"text": "आधा दे दो", "correct": False}]}),
                    "tool_suggestion": "savings_goal", "xp_reward": 10, "order_index": 1
                },
                {
                    "title_en": "The 50-30-20 Budget Rule",
                    "title_hi": "50-30-20 बजट नियम",
                    "story_en": "Anita earns ₹15,000 per month. She uses a simple rule: 50% (₹7,500) for needs — rent, food, bills. 30% (₹4,500) for wants — clothes, outings, mobile recharge. 20% (₹3,000) for savings. Even if your income is ₹5,000, you can use this rule. Needs first, then wants, always save something.",
                    "story_hi": "अनिता ₹15,000 महीना कमाती है। वह एक सरल नियम अपनाती है: 50% (₹7,500) ज़रूरतों पर — किराया, खाना, बिल। 30% (₹4,500) इच्छाओं पर — कपड़े, घूमना। 20% (₹3,000) बचत। ₹5,000 आय हो तब भी यह नियम काम करता है।",
                    "takeaway_en": "Spend 50% on needs, 30% on wants, save 20%. Adjust based on your income.",
                    "takeaway_hi": "50% ज़रूरत, 30% इच्छा, 20% बचत। अपनी आय के हिसाब से बदलें।",
                    "scenario_en": json.dumps({"question": "You earn ₹10,000/month. How much should you try to save?", "options": [{"text": "Nothing — income is too low", "correct": False}, {"text": "At least ₹2,000 (20%)", "correct": True}, {"text": "₹8,000 — save everything", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "₹10,000 महीना कमाते हैं। कितना बचाएं?", "options": [{"text": "कुछ नहीं — आय कम है", "correct": False}, {"text": "कम से कम ₹2,000 (20%)", "correct": True}, {"text": "₹8,000 — सब बचाओ", "correct": False}]}),
                    "tool_suggestion": "budget_tool", "xp_reward": 10, "order_index": 2
                }
            ]
        },
        # ============================
        # INTERMEDIATE — CREDIT
        # ============================
        {
            "pillar": "credit", "level": "intermediate",
            "title_en": "Understanding EMI & Credit Score", "title_hi": "EMI और क्रेडिट स्कोर समझें",
            "description_en": "Learn how EMI works and why credit score matters", "description_hi": "EMI कैसे काम करता है और क्रेडिट स्कोर क्यों ज़रूरी",
            "order_index": 6,
            "lessons": [
                {
                    "title_en": "EMI — Small Payments, Big Purchases",
                    "title_hi": "EMI — छोटी किस्त, बड़ी खरीदारी",
                    "story_en": "EMI means Equal Monthly Installment. Instead of paying ₹60,000 at once for a phone, you pay ₹5,000 per month for 12 months. But remember — EMI includes interest! You might end up paying ₹62,000 total. EMI is helpful but only buy what you truly need. Paying EMI on time builds your credit score — your financial reputation.",
                    "story_hi": "EMI का मतलब है समान मासिक किस्त। ₹60,000 का फोन एक बार में खरीदने की जगह ₹5,000 हर महीने 12 महीने तक। लेकिन याद रखें — EMI में ब्याज शामिल है! कुल ₹62,000 चुकाने पड़ सकते हैं। EMI उपयोगी है लेकिन सिर्फ ज़रूरत की चीज़ खरीदें। समय पर EMI चुकाने से क्रेडिट स्कोर बनता है।",
                    "takeaway_en": "EMI helps spread cost but includes interest. Pay on time to build credit score.",
                    "takeaway_hi": "EMI खर्च बाँटती है लेकिन ब्याज लगता है। समय पर चुकाएं।",
                    "scenario_en": json.dumps({"question": "You want a ₹30,000 phone on EMI. Your monthly income is ₹12,000. Good idea?", "options": [{"text": "Yes — EMI makes it affordable", "correct": False}, {"text": "No — EMI would be too large for your income", "correct": True}, {"text": "Buy two phones on EMI", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "₹30,000 का फोन EMI पर चाहिए। आय ₹12,000 है। सही है?", "options": [{"text": "हाँ — EMI से affordable है", "correct": False}, {"text": "नहीं — EMI आय के हिसाब से ज़्यादा होगी", "correct": True}, {"text": "दो फोन EMI पर लो", "correct": False}]}),
                    "tool_suggestion": "emi_calculator", "xp_reward": 10, "order_index": 1
                }
            ]
        },
        # ============================
        # INTERMEDIATE — INVESTMENTS
        # ============================
        {
            "pillar": "investments", "level": "intermediate",
            "title_en": "Beyond FD — More Ways to Grow Money", "title_hi": "FD से आगे — पैसे बढ़ाने के और तरीके",
            "description_en": "Learn about RD, SIP, and gold investments", "description_hi": "RD, SIP और सोने में निवेश जानें",
            "order_index": 7,
            "lessons": [
                {
                    "title_en": "Recurring Deposit & SIP — Save Monthly, Grow Yearly",
                    "title_hi": "RD और SIP — हर महीने बचाओ, हर साल बढ़ाओ",
                    "story_en": "Sunita can't save ₹10,000 at once. But she can save ₹1,000 every month. She puts ₹500 in Recurring Deposit (RD) — fixed interest, guaranteed. And ₹500 in SIP (Systematic Investment Plan) in a mutual fund — higher potential returns but some risk. After 3 years, her RD gave steady returns. Her SIP grew even more. Combining safe and growth investments is smart.",
                    "story_hi": "सुनीता एक बार में ₹10,000 नहीं बचा सकती। लेकिन हर महीने ₹1,000 बचा सकती है। ₹500 RD में — निश्चित ब्याज। ₹500 SIP में — ज़्यादा संभावित रिटर्न लेकिन थोड़ा जोखिम। 3 साल बाद RD ने स्थिर रिटर्न दिया। SIP ने और ज़्यादा बढ़ाया।",
                    "takeaway_en": "RD is safe monthly saving. SIP gives higher returns with some risk. Use both.",
                    "takeaway_hi": "RD सुरक्षित मासिक बचत। SIP ज़्यादा रिटर्न लेकिन थोड़ा जोखिम। दोनों करें।",
                    "scenario_en": json.dumps({"question": "You can save ₹1,000/month. How should you invest?", "options": [{"text": "All in one risky scheme", "correct": False}, {"text": "Split between RD (safe) and SIP (growth)", "correct": True}, {"text": "Don't invest — just keep cash", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "₹1,000/महीना बचा सकते हैं। कैसे निवेश करें?", "options": [{"text": "सब एक जोखिम वाली योजना में", "correct": False}, {"text": "RD (सुरक्षित) और SIP (बढ़ोतरी) में बाँटो", "correct": True}, {"text": "निवेश मत करो — नकद रखो", "correct": False}]}),
                    "tool_suggestion": None, "xp_reward": 10, "order_index": 1
                }
            ]
        },
        # ============================
        # INTERMEDIATE — SMALL BUSINESS
        # ============================
        {
            "pillar": "small_business", "level": "intermediate",
            "title_en": "Pricing & Profit Calculation", "title_hi": "मूल्य निर्धारण और लाभ गणना",
            "description_en": "Learn to calculate actual profit in your business", "description_hi": "अपने व्यापार में असली लाभ गिनना सीखें",
            "order_index": 8,
            "lessons": [
                {
                    "title_en": "Are You Really Making Profit?",
                    "title_hi": "क्या आप सच में मुनाफा कमा रहे हैं?",
                    "story_en": "Raju sells samosas for ₹10 each. He thinks he earns good money. But when he counts his costs — flour ₹3, oil ₹2, gas ₹1, vegetables ₹2 = ₹8 total cost. His real profit is only ₹2 per samosa. If he sells 100 samosas, his real profit is ₹200, not ₹1,000. Many small business owners confuse revenue (total sales) with profit (what's left after costs).",
                    "story_hi": "राजू ₹10 में समोसा बेचता है। उसे लगता है अच्छा कमा रहा है। लेकिन खर्चा गिनें — आटा ₹3, तेल ₹2, गैस ₹1, सब्ज़ी ₹2 = कुल ₹8। असली मुनाफा सिर्फ ₹2 प्रति समोसा। 100 समोसे बेचे तो ₹200 मुनाफा, ₹1,000 नहीं।",
                    "takeaway_en": "Profit = Sales - All Costs. Always count every cost including your time.",
                    "takeaway_hi": "मुनाफा = बिक्री - सारे खर्चे। हर खर्चा गिनें।",
                    "scenario_en": json.dumps({"question": "You sell items for ₹500 total today. Your costs were ₹400. What is your profit?", "options": [{"text": "₹500 — that's what I earned", "correct": False}, {"text": "₹100 — sales minus costs", "correct": True}, {"text": "₹400 — that's what I spent", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "आज ₹500 की बिक्री। खर्चा ₹400। मुनाफा कितना?", "options": [{"text": "₹500 — इतना कमाया", "correct": False}, {"text": "₹100 — बिक्री से खर्चा घटाओ", "correct": True}, {"text": "₹400 — इतना खर्च किया", "correct": False}]}),
                    "tool_suggestion": "budget_tool", "xp_reward": 10, "order_index": 1
                }
            ]
        },
        # ============================
        # ADVANCED — SAVINGS
        # ============================
        {
            "pillar": "savings", "level": "advanced",
            "title_en": "Tax Saving & Long-term Goals", "title_hi": "कर बचत और दीर्घकालिक लक्ष्य",
            "description_en": "Learn about tax-saving investments and planning for future", "description_hi": "कर बचत निवेश और भविष्य की योजना सीखें",
            "order_index": 9,
            "lessons": [
                {
                    "title_en": "PPF & Tax Saving — Government Helps You Save",
                    "title_hi": "PPF और कर बचत — सरकार बचत में मदद करती है",
                    "story_en": "The government wants you to save money. That's why they created PPF (Public Provident Fund). You put money in PPF and get: 7-8% interest (better than savings account), tax saving under Section 80C, and your money is completely safe with government guarantee. PPF locks money for 15 years, but you can partially withdraw after 7 years. It's perfect for children's education or retirement.",
                    "story_hi": "सरकार चाहती है कि आप बचत करें। इसलिए PPF बनाया। PPF में पैसे डालें: 7-8% ब्याज, Section 80C में कर बचत, और सरकारी गारंटी से पूर्ण सुरक्षा। 15 साल का लॉक-इन लेकिन 7 साल बाद आंशिक निकासी। बच्चों की पढ़ाई या रिटायरमेंट के लिए बेहतरीन।",
                    "takeaway_en": "PPF gives safety + tax saving + good returns. Ideal for long-term goals.",
                    "takeaway_hi": "PPF — सुरक्षा + कर बचत + अच्छा रिटर्न। दीर्घकालिक लक्ष्यों के लिए आदर्श।",
                    "scenario_en": json.dumps({"question": "You want to save for your child's college (15 years away). Best option?", "options": [{"text": "Keep cash at home", "correct": False}, {"text": "Invest in PPF for tax saving and guaranteed returns", "correct": True}, {"text": "Buy gold jewellery", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "बच्चे के कॉलेज (15 साल बाद) के लिए बचत। सबसे अच्छा?", "options": [{"text": "घर पर नकद रखो", "correct": False}, {"text": "PPF में निवेश करो — कर बचत और गारंटीड रिटर्न", "correct": True}, {"text": "सोने के गहने खरीदो", "correct": False}]}),
                    "tool_suggestion": "savings_goal", "xp_reward": 10, "order_index": 1
                }
            ]
        },
        # ============================
        # ADVANCED — CREDIT
        # ============================
        {
            "pillar": "credit", "level": "advanced",
            "title_en": "Credit Score & Smart Borrowing", "title_hi": "क्रेडिट स्कोर और स्मार्ट उधारी",
            "description_en": "Master credit score management and loan strategies", "description_hi": "क्रेडिट स्कोर प्रबंधन और लोन रणनीतियाँ सीखें",
            "order_index": 10,
            "lessons": [
                {
                    "title_en": "Your Credit Score — Your Financial Reputation",
                    "title_hi": "क्रेडिट स्कोर — आपकी वित्तीय प्रतिष्ठा",
                    "story_en": "Credit score is a number (300-900) that shows how trustworthy you are with money. Banks check it before giving loans. Score above 750 = easy loans at low interest. Score below 600 = loans rejected or high interest. How to build good score: Pay EMIs on time, don't take too many loans, use credit card wisely, check your score yearly for free on CIBIL website.",
                    "story_hi": "क्रेडिट स्कोर (300-900) बताता है कि आप पैसों के मामले में कितने भरोसेमंद हैं। 750 से ऊपर = आसान लोन कम ब्याज पर। 600 से नीचे = लोन नहीं मिलता या महंगा। अच्छा स्कोर बनाएं: EMI समय पर दें, ज़्यादा लोन न लें, क्रेडिट कार्ड समझदारी से इस्तेमाल करें।",
                    "takeaway_en": "Pay on time, borrow wisely, check score yearly. Good score = cheaper loans.",
                    "takeaway_hi": "समय पर चुकाएं, समझदारी से उधार लें। अच्छा स्कोर = सस्ता लोन।",
                    "scenario_en": json.dumps({"question": "Your credit score is 650. You want a home loan. What should you do first?", "options": [{"text": "Apply anyway and hope for the best", "correct": False}, {"text": "Pay off existing debts and improve score above 750 first", "correct": True}, {"text": "Borrow from moneylender instead", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "क्रेडिट स्कोर 650 है। होम लोन चाहिए। पहले क्या करें?", "options": [{"text": "फिर भी अप्लाई करो", "correct": False}, {"text": "पहले मौजूदा कर्ज चुकाओ और स्कोर 750 से ऊपर लाओ", "correct": True}, {"text": "साहूकार से ले लो", "correct": False}]}),
                    "tool_suggestion": "emi_calculator", "xp_reward": 10, "order_index": 1
                }
            ]
        },
        # ============================
        # ADVANCED — INVESTMENTS
        # ============================
        {
            "pillar": "investments", "level": "advanced",
            "title_en": "Diversification & Risk Management", "title_hi": "विविधीकरण और जोखिम प्रबंधन",
            "description_en": "Learn to spread investments and manage risk", "description_hi": "निवेश फैलाना और जोखिम प्रबंधित करना सीखें",
            "order_index": 11,
            "lessons": [
                {
                    "title_en": "Don't Put All Eggs in One Basket",
                    "title_hi": "सारे अंडे एक टोकरी में न रखें",
                    "story_en": "Vikram invested all his ₹1,00,000 in one company's shares. The company failed. He lost everything. His friend Amit split his money: ₹30,000 in FD, ₹30,000 in mutual fund SIP, ₹20,000 in gold, ₹20,000 in PPF. When one investment went down, others went up. Amit's money was safe overall. This is called diversification — spreading money across different investments to reduce risk.",
                    "story_hi": "विक्रम ने अपने सारे ₹1,00,000 एक कंपनी के शेयर में लगाए। कंपनी डूब गई। सब खो दिया। उसके दोस्त अमित ने बाँटा: ₹30,000 FD, ₹30,000 SIP, ₹20,000 सोना, ₹20,000 PPF। एक निवेश गिरा तो दूसरा बढ़ा। अमित के पैसे कुल मिलाकर सुरक्षित रहे। इसे विविधीकरण कहते हैं।",
                    "takeaway_en": "Spread investments across FD, SIP, gold, PPF. Never put all money in one place.",
                    "takeaway_hi": "FD, SIP, सोना, PPF में बाँटें। सारा पैसा एक जगह न लगाएं।",
                    "scenario_en": json.dumps({"question": "You have ₹50,000 to invest. Best approach?", "options": [{"text": "Put everything in cryptocurrency", "correct": False}, {"text": "Spread across FD, SIP, and gold", "correct": True}, {"text": "Keep all as cash at home", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "₹50,000 निवेश करने हैं। सबसे अच्छा तरीका?", "options": [{"text": "सब cryptocurrency में डालो", "correct": False}, {"text": "FD, SIP और सोने में बाँटो", "correct": True}, {"text": "सब नकद घर पर रखो", "correct": False}]}),
                    "tool_suggestion": None, "xp_reward": 10, "order_index": 1
                }
            ]
        },
        # ============================
        # ADVANCED — SMALL BUSINESS
        # ============================
        {
            "pillar": "small_business", "level": "advanced",
            "title_en": "Cash Flow & Business Growth", "title_hi": "कैश फ्लो और व्यापार वृद्धि",
            "description_en": "Understand cash flow management and scaling your business", "description_hi": "कैश फ्लो प्रबंधन और व्यापार बढ़ाना सीखें",
            "order_index": 12,
            "lessons": [
                {
                    "title_en": "Cash Flow — Why Profitable Businesses Fail",
                    "title_hi": "कैश फ्लो — मुनाफे वाले व्यापार क्यों डूबते हैं",
                    "story_en": "Profit does not mean cash in hand. Deepak's furniture shop gets big orders. Customers pay after 30 days. But Deepak needs to buy wood today. He has profit on paper but no cash to run the business. This is called cash flow problem. Cash flow means money coming in and going out daily. A business can be profitable but still fail if cash is not managed properly. Always keep some cash reserve for daily operations.",
                    "story_hi": "मुनाफा मतलब हाथ में पैसा नहीं। दीपक की फर्नीचर दुकान पर बड़े ऑर्डर आते हैं। ग्राहक 30 दिन बाद भुगतान करते हैं। लेकिन दीपक को आज लकड़ी खरीदनी है। कागज़ पर मुनाफा है लेकिन चलाने के लिए पैसा नहीं। इसे कैश फ्लो समस्या कहते हैं। रोज़ के काम के लिए कुछ नकद हमेशा रखें।",
                    "takeaway_en": "Cash flow ≠ profit. Keep cash reserve for daily operations. Get payments faster.",
                    "takeaway_hi": "कैश फ्लो ≠ मुनाफा। रोज़ के काम के लिए नकद रखें।",
                    "scenario_en": json.dumps({"question": "Your business is profitable but you can't pay this month's rent. What happened?", "options": [{"text": "The business is failing", "correct": False}, {"text": "Cash flow problem — money is stuck with customers", "correct": True}, {"text": "Rent is too expensive", "correct": False}]}),
                    "scenario_hi": json.dumps({"question": "व्यापार में मुनाफा है लेकिन इस महीने का किराया नहीं दे पा रहे। क्या हुआ?", "options": [{"text": "व्यापार डूब रहा है", "correct": False}, {"text": "कैश फ्लो समस्या — पैसा ग्राहकों के पास अटका है", "correct": True}, {"text": "किराया बहुत ज़्यादा है", "correct": False}]}),
                    "tool_suggestion": "budget_tool", "xp_reward": 10, "order_index": 1
                }
            ]
        }
    ]

    # Insert all modules and lessons
    for mod_data in modules_data:
        lessons = mod_data.pop("lessons")
        module = Module(**mod_data)
        db.add(module)
        db.flush()  # Get module.id

        for lesson_data in lessons:
            lesson = Lesson(module_id=module.id, **lesson_data)
            db.add(lesson)

    db.commit()
    print(f"✅ Seeded {len(modules_data)} modules with lessons!")
    db.close()

if __name__ == "__main__":
    seed()
