import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Pivot! Ross's Best Friends Moments Compilation",
        "Monica's Cleanest OCD Moments That Will Make You Laugh",
        "Joey Doesn't Share Food! Best Joey Moments",
        "We Were on a Break! Ross & Rachel Arguments Ranked",
        "Chandler's Funniest One-Liners - Friends TV Show",
        "Smelly Cat! Phoebe's Most Iconic Moments",
        "The One Where... All the Best Cold Opens",
        "Friends Bloopers You've Never Seen Before",
        "How YOU Doin'? Joey's Best Pickup Lines",
        "Unagi! Ross's Funniest Obsessions",
        "Monica's Secret Closet - The Mess We Never See",
        "Chandler Bing's Best Sarcastic Moments Compilation",
        "Friends - The Funniest Arguments of All Time",
        "Central Perk's Best Moments - Friends TV Show",
        "Friends Christmas Episodes - Holiday Special Compilation",
    ]

    fallback_descriptions = [
        "Could this BE any more iconic? 🛋️ We're bringing you the absolute best moments from Friends - the show that defined a generation. From Ross's 'PIVOT!' to Joey's 'How YOU doin'?' - every second is pure gold. Which character is your favorite? Drop their name in the comments! ⬇️ #friends #friendstv #friendsTVshow #friendsfan #rossgeller #joeytribbiani #monicageller #chandlerbing #phoebebuffay #rachelgreen #tvshow #funny",
        "MONICA! 🧹 If you know, you know. We're counting down the most hilarious Monica Geller moments that prove she's the funniest perfectionist on TV. From her secret closet to her legendary Thanksgiving disasters - she's pure entertainment. Tag someone who is SO Monica in your life! 👇 #monicageller #friends #courteneycox #friendstv #monicagelleriscrazy #tvhumor #friendsTV #90sshow #comedyshow",
        "Joey Tribbiani doesn't share food! 🍕 We're counting down the funniest Joey moments from all 10 seasons of Friends. From his acting auditions to his sandwich obsession — this compilation will have you crying with laughter. Which Joey moment is your favorite? Tell us below! 👇 #joeytribbiani #friends #friendstv #mattleblanc #howyoudoin #funny #tvshow #90sshow #friendscompilation",
        "Ross Geller's dinosaur obsession is unmatched! 🦖 From his paleontology rants to his 'we were on a break' mantra — we've compiled the absolute best Ross moments. David Schwimmer's comedic timing is pure genius. Like if Ross is your favorite character! 👍 #rossgeller #friends #davidschwimmer #friendsTV #pivot #dinosaurs #unagi #tvcomedy",
        "Oh. My. GOD. 😱 Janice! We're celebrating the most iconic recurring character in Friends history. From her unforgettable 'OH. MY. GOD!' to her hilarious appearances throughout the series. Janice Litman Goralnik née Hosenstein deserves her own spin-off! Comment your favorite Janice moment! 💬 #janice #friendstv #friends #OHMYGOD #maggiewheeler #tvshow #90scomedy",
        "Chandler Bing's sarcasm is an art form 🎭 We've curated the most savage and hilarious one-liners from the king of wit. 'Could I BE any more...' Fill in the blank in the comments! This compilation will have you quoting Chandler all day. Save for a laugh! 😂 #chandlerbing #friends #matthewperry #sarcasm #couldIbe anymore #friendsTV #funnyquotes",
        "Rachel Greene's fashion evolution 👗 From Central Perk waitress to Ralph Lauren executive — we're looking back at Rachel's most iconic looks and funniest moments. Jennifer Aniston brought so much heart (and hilarious crying) to this role. Which Rachel haircut was your favorite? ✂️ #rachelgreene #friends #jenniferaniston #friendsfashion #90sfashion #tvshow #rachelhairstyle",
        "Phoebe Buffay's Smelly Cat and her most unhinged moments 🐱🎸 From her eerie songs to her unpredictable stories — Lisa Kudrow's Phoebe is truly one of a kind. This compilation proves she's the wild card that made Friends perfect. Tag your friend who is SO Phoebe! ✨ #phoebebuffay #friends #lisakudrow #smellycat #friendsTV #quirky #tvshow",
        "Friends Thanksgiving Episodes 🦃 We're serving up the best Thanksgiving moments from the show that made this holiday legendary. The trifle, the football game, the pants that were too tight... which Thanksgiving episode is your favorite? Vote in the comments! 🏈 #friendsthanksgiving #friends #tvshow #holiday #trifle #thanksgiving #friendstv",
        "The Funniest Cold Opens from Friends 🚪 The first 2 minutes of every episode were pure comedy gold. From Monica's 'Welcome to the real world! It sucks!' to Ross's leather pants disaster. We've compiled the absolute best cold opens that will make you want to binge the entire series again. Like if you agree! 📺 #friendscoldopens #friends #tvshow #90sTV #funny",
        "Ross and Rachel - The Ultimate Relationship Timeline 💔❤️ From their first kiss at Central Perk to the final 'I got off the plane' — we're recapping the most emotional, dramatic, and hilarious moments of TV's most iconic couple. Team Ross or Team Rachel? Tell us in the comments! ⬇️ #rossandrachel #friends #weareonabreak #tvshow #romance #iconiccouple",
        "Central Perk - The REAL Main Character ☕ The orange couch, the coffee mugs, the live music from Phoebe — Central Perk was more than just a coffee shop, it was a character in itself. Here's every iconic moment that happened at that legendary couch. Share with a fellow Friends fan! 🛋️ #centralperk #friends #coffee #TVshow #nyc #greenday",
        "Did Monica and Chandler really work as a couple? 🔥 We're breaking down the BEST moments from the most unexpected (and beloved) relationship in the show. From London hookup to adopting twins — their love story was GOALS. Drop a ❤️ if you ship Mondler! #monicaandchandler #mondler #friends #courteneycox #matthewperry #friendsTV #couplegoals",
        "The One Where We Rank ALL the Guest Stars ⭐ Friends had some amazing guest stars: Brad Pitt, Julia Roberts, Bruce Willis, Reese Witherspoon, and SO many more. We're counting down the most memorable celebrity cameos in the show's history. Which guest star was your favorite? Comment below! 🎬 #friendsgueststars #friends #bradpitt #juliaroberts #tvshow #cameo",
        "Gunther - The Unsung Hero of Friends ☕️ From his unrequited love for Rachel to his Central Perk apron — Gunther was the background character who stole our hearts. Here's a tribute to the best supporting character in TV history. Rest in peace, James Michael Tyler. 🕊️ #gunther #friends #centralperk #jamestyler #tvshow #unsunghero",
        "Friends Bloopers and Behind the Scenes 🤣 The cast of Friends had UNBELIEVABLE chemistry — and these bloopers prove it. From cast members breaking character to improvised lines that made the final cut. This behind-the-scenes compilation will warm your heart. Tag a Friends fan who NEEDS to see this! 🎬 #friendsbloopers #behindthescenes #friends #friendscast #laughs",
        "Which Friends Character Are You? 🧐 Take our quiz by watching these character-defining moments! Are you a Monica (organized perfectionist), a Rachel (fashion-forward heart), a Phoebe (quirky free spirit), a Chandler (sarcastic but sweet), a Joey (food-loving loyal friend), or a Ross (nerdy but romantic)? Tell us your result! 🏆 #friendsquiz #whichfriendscharacterareyou #friends #tvshow #personality",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "funny and nostalgic — take fans back to the best moments of the show",
        "energetic and exciting — get viewers hyped about classic scenes",
        "warm and sentimental — remind fans why they love this show so much",
        "humorous and witty — highlight the comedy gold of the characters",
        "engaging and interactive — get fans debating their favorite moments",
        "fast-paced and punchy — deliver laughs in quick succession",
        "celebratory and appreciative — honor the legacy of the show",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Friends TV Funny'. "
        f"The page is dedicated to the hit TV show Friends — celebrating the funniest moments, iconic scenes, character compilations, and nostalgic memories of Monica, Chandler, Joey, Ross, Rachel, and Phoebe. "
        f"It's hilarious, nostalgic, and perfect for any fan of the show. "
        f"Speak as a passionate Friends fan who knows every episode by heart and loves sharing the best moments. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), fun, and engaging for fellow fans. "
        f"Include engagement calls-to-action such as: "
        f"- Like if this is your favorite Friends moment! "
        f"- Comment your favorite character below! "
        f"- Share with a fellow Friends fan! "
        f"- Follow Friends TV Funny for more hilarious compilations! "
        f"Include relevant hashtags in ALL LOWERCASE such as #friends #friendstv #friendsTVshow #friendsfan #rossgeller #joeytribbiani #monicageller #chandlerbing #phoebebuffay #rachelgreen #tvshow #funny #90sshow. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["friends", "friendstv", "friendsTVshow", "rossgeller", "joeytribbiani", "monicageller", "chandlerbing", "phoebebuffay", "rachelgreen", "tvshow", "funny", "90sshow", "friendscompilation", "friendsmoments"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
