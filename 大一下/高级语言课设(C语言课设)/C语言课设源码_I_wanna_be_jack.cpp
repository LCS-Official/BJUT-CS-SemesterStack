#include <graphics.h>
#include <iostream>
#include <Windows.h>
#include <string>
#include <fstream>               // For io fun
#include <vector>
#include <algorithm>             //For sort() fun
#include <random>                //For twister fun
#include <thread>
#pragma comment(lib, "Winmm.lib")//For playing sound effects
using namespace std;

struct Player {
    double x, y;
    double velocityY;
    bool isJumping;
    bool isMovingLeft;
    bool isMovingRight;
    bool isSpacePressed;  // 空格键是否被按下
    bool isOnGround;      // 是否在地面上
    int jumpCount;        // 跳跃次数
    bool isdead;
    bool iswin = 0;
    int coins = 0;
    int difficlty = 2;
    int plrsize = 60;
};

// 结构体用于存储用户信息
struct UserData {
    string username;
    int coins;
};

struct GameEssentials {
    const float gravity = 0.4;
    const int jump_speed = 10;
    const int move_speed = 5;
    const int window_width = 1462;
    const int window_height = 800;
    const int move_speed_Y = 5;//背景移动速度
    const int spike_size = 30;

    bool isMouseControlEnabled = 0;
    int cur_plr_anime_index = 0;
    const int plr_anime_num = 3;//plr动画总数
    bool namesandcoinssaved = 0;//是否已保存数据
    int curspikecnt = 0;
    bool isplanecrash = 0;
    bool isPaused = false; // 用于跟踪游戏是否处于暂停状态
    DWORD lastPauseToggleTime = 0; // 定义并初始化上次切换暂停状态的时间变量
    bool death_sfx_played = 0;
    int musicplaying = 0;
    bool createstartscreen = 1;//是否创建新的开始界面 保证开始界面只跳出一次
    bool playedcurBGM = 0;
};

// 定义刺
struct Spike {
    float x1;
    float y1;//仅记录左上角坐标
    int species;//刺的种类
    bool eaten;//是否被食用
    bool ismissioncomplete;//是否已经移动到屏幕外
    bool hasResetPosition;//向下移动的刺是否已重置到顶端
    Spike* next;
};

//难度获取
int getDifficulty() {
    int diff = 0;
    bool validInput = false;
    while (!validInput) {
        TCHAR difficulty[2];
        bool diffres = InputBox(difficulty, 2, L"在下面输入难度(难度为1~3档):", L"你希望在哪个难度下进行游戏", NULL, 300, 200);
        wstring diffWStr = difficulty;
        diff = stoi(diffWStr);
        if (diff >= 1 && diff <= 3) {
            validInput = true;
        }
        else {
            MessageBox(NULL, L"请输入1到3之间的数字！", L"错误", MB_ICONERROR | MB_OK);
        }
    }
    return diff;
}

// 从文件中读取用户信息并存储到结构体数组中
vector<UserData> readUserDataFromFile(const string& filePath) {
    ifstream inFile(filePath);
    vector<UserData> userDataVec;
    if (inFile.is_open()) {
        string username;
        int coins;
        while (inFile >> username >> coins) {
            UserData userData;
            userData.username = username;
            userData.coins = coins;
            userDataVec.push_back(userData);
        }
        inFile.close();
    }
    else {
        MessageBox(NULL, L"Error: Unable to open file for reading!", L"错误", MB_ICONERROR | MB_OK);
    }
    return userDataVec;
}

// 比较函数，用于排序
bool compareByCoins(const UserData& userData1, const UserData& userData2) {
    // 按照金币数量降序排序
    return userData1.coins > userData2.coins;
}

// 对用户信息按照金币数量进行排序
void sortUserDataByCoins(vector<UserData>& userDataVec) {
    sort(userDataVec.begin(), userDataVec.end(), compareByCoins);
}

// 显示排行榜
void displayLeaderboard(const vector<UserData>& userDataVec) {
    // 构建排行榜信息字符串
    string leaderboardMsg = "Rank\tUsername\t\tCoins\n";
    int range = (userDataVec.size() <= 10) ? userDataVec.size() : 10;
    for (size_t i = 0; i < range; ++i) {
        string rank = to_string(i + 1);
        string username = userDataVec[i].username;
        string coins = to_string(userDataVec[i].coins);
        leaderboardMsg += rank + "\t" + username + "\t\t" + coins + "\n";
    }

    // 将string转换为wchar_t*
    int size_needed = MultiByteToWideChar(CP_UTF8, 0, leaderboardMsg.c_str(), -1, NULL, 0);
    wstring leaderboardMsgWide(size_needed, 0);
    MultiByteToWideChar(CP_UTF8, 0, leaderboardMsg.c_str(), -1, &leaderboardMsgWide[0], size_needed);

    // 显示MessageBox
    MessageBox(NULL, leaderboardMsgWide.c_str(), L"排行榜(前10名)", MB_OK | MB_ICONINFORMATION);
}

//reset
void resetVariables(Spike*& head, GameEssentials game) {
    game.cur_plr_anime_index = 0;
    game.namesandcoinssaved = false;
    game.curspikecnt = 0;
    game.isplanecrash = false;
    game.isPaused = 0;
    game.death_sfx_played = 0;
    game.musicplaying = 0;

    while (head != nullptr) {
        Spike* temp = head;
        head = head->next;
        delete temp;
    }
}

//教程窗口
void givetutorial() {
    MessageBox(NULL, L"使用AD或者鼠标左右键左右移动\n使用空格键或者鼠标中键跳跃\n吃到浆果可以恢复二段跳的能力\n蘑菇带有魔法\n捕获盲盒可以随机获得金币或能力\n要注意躲避尖刺\n祝你玩得愉快！", L"游戏教程", MB_ICONINFORMATION | MB_OK);
}

// 加载背景图像
IMAGE background;

//去除图像黑边
inline void putimage_alpha(int x, int y, IMAGE* img) {
    int w = img->getwidth();
    int h = img->getheight();
    AlphaBlend(GetImageHDC(NULL), x, y, w, h,
        GetImageHDC(img), 0, 0, w, h, { AC_SRC_OVER,0,255,AC_SRC_ALPHA });
}

// 绘制背景
void drawBackground(IMAGE& background, double& bgPosY) {
    putimage(0, bgPosY, &background); // 绘制背景图片，位置从左上角开始
}

// 清除指定位置的文本
void clearText(int x, int y, int textWidth, int textHeight) {
    // 设置文本背景模式为透明
    setbkmode(TRANSPARENT);
}

// 实时展示金币数量，并清除之前的文本
void displayCoinValue(int x, int y, Player player, int factor) {
    // 将变量的值转换为字符串
    wstring coinnum = to_wstring(player.coins);

    // 设置文本颜色为黑色
    settextcolor(BLACK);

    if (factor == 1) {
        coinnum = L"金币数：" + coinnum;
        settextstyle(25, 0, _T("宋体"));
    }
    else {
        coinnum = L"总共获得" + coinnum + L"个金币";
        settextstyle(40, 0, _T("宋体"));
    }

    TCHAR* s = new TCHAR[coinnum.length() + 1];
    copy(coinnum.begin(), coinnum.end(), s);
    s[coinnum.length()] = '\0'; // 添加字符串结束符

    outtextxy(x, y, s);

    // 清除之前的文本
    int textWidth = textwidth(s);
    int textHeight = textheight(s);
    clearText(x, y, textWidth, textHeight);
}

string getUsernameFromInput(Player player) {
    // 显示输入框，并获取用户名
    TCHAR username[8]; // 创建一个缓冲区来存储用户名，假设最大长度为 8
    bool result = (player.isdead) ? InputBox(username, 8, L"在下面输入用户名(仅支持字母、数字与下划线或点的组合):", L"Jack死了！请输入用户名，系统将自动存储金币！", NULL, 300, 200) :
        InputBox(username, 8, L"在下面输入用户名(仅支持字母、数字与下划线或点的组合):", L"Jack到达了终点！", NULL, 300, 200);

    wstring usernameWStr = username;
    string usernameStr(usernameWStr.begin(), usernameWStr.end());

    // 返回输入的用户名
    return usernameStr;
}

void saveUsernameToFile(Player player, const string& username, const string& filePath) {
    ofstream outFile(filePath, ios::app); // 打开文件以追加写入模式
    if (outFile.is_open()) {
        outFile << username << " " << player.coins << endl; // 存储用户名并添加换行符
        outFile.close();
    }
    else {
        MessageBox(NULL, L"Error: Unable to open file for reading!", L"错误", MB_ICONERROR | MB_OK);
    }
}

bool checkIfUsernameExists(const string& filePath, const string& newUsername) {
    ifstream inFile(filePath);
    string username;

    if (inFile.is_open()) {
        bool exists = false; // 添加一个标志来记录是否找到相同的用户名
        // 逐行读取文件内容，检查是否存在重复用户名
        while (getline(inFile, username)) {
            //cout << username << " ";
            if (username == newUsername) { // 比较读取到的用户名与要检查的用户名
                exists = true; // 如果找到相同的用户名，将标志设为true
                //cout << exists << " ";
                break; // 找到相同的用户名后直接退出循环，不再继续查找
            }
        }
        inFile.close();

        return exists; // 返回标志来表示是否找到相同的用户名
    }
    else {
        MessageBox(NULL, L"Error: Unable to open file for reading!", L"错误", MB_ICONERROR | MB_OK);
        return false; // 如果无法打开文件，则返回false
    }
}

//角色死亡，播放动画以及展示横幅
void plrdeath(Player player,GameEssentials& game) {
    if (player.isdead) {
        // 绘制横幅
        IMAGE bannerImage;
        const wchar_t* bannerImagePath = L"图片素材/Miscellaneous/banner_slain.png";
        loadimage(&bannerImage, bannerImagePath);
        putimage_alpha(163, 300, &bannerImage);
        displayCoinValue(560, 500, player, 2);

        if (!game.death_sfx_played) {
            // 播放音乐
            PlaySound(L"音频素材/sfx/plr_deathnew_sfx.wav", NULL, SND_FILENAME | SND_ASYNC);
            Sleep(1200);
            // 停止音乐
            PlaySound(NULL, 0, 0);

            game.death_sfx_played = 1;
        }
    }
    if (player.iswin) {
        // 绘制横幅
        IMAGE bannerImage;
        const wchar_t* bannerImagePath = L"图片素材/Miscellaneous/banner_victory.png";
        loadimage(&bannerImage, bannerImagePath);
        putimage_alpha(163, 300, &bannerImage);
        displayCoinValue(560, 500, player, 2);
    }
}

int movecnt = 0;//用于增加金币
// 移动背景
void moveBackground(double& bgPosY, Player player, GameEssentials game) {
    double bgmovespeed;
    switch (player.difficlty){
    case 1:
        bgmovespeed = 0.5;
        break;
    case 2:
        bgmovespeed = 0.35;
        break;
    case 3:
        bgmovespeed = 0.15;
        break;
    }
    bgPosY -= bgmovespeed * game.move_speed_Y;//控制背景下落速度
    movecnt++;
}

void drawJumpCnt(Player player) {
    IMAGE logo;
    if (player.jumpCount == 2) {
        loadimage(&logo, L"图片素材/Miscellaneous/jump_status_false.png");
    }
    else {
        loadimage(&logo, L"图片素材/Miscellaneous/jump_status_true.png");
    }
    putimage_alpha(0, 0, &logo);
}

// 加载玩家图像
IMAGE playerLeft[3], playerRight[3];
IMAGE playerLefts[3], playerRights[3];

//加载动画
void loadanime(GameEssentials game) {
    for (size_t i = 0; i < game.plr_anime_num; i++) {
        //使用拼接字符串的方法引入类似名称的图片
        wstring left_path = L"图片素材/Miscellaneous/kid_left" + wstring(1, L'0' + i + 1) + L".png";
        wstring right_path = L"图片素材/Miscellaneous/kid_right" + wstring(1, L'0' + i + 1) + L".png";
        loadimage(&playerLeft[i], left_path.c_str());
        loadimage(&playerRight[i], right_path.c_str());
    }
    for (size_t i = 0; i < game.plr_anime_num; i++) {
        wstring left_path = L"图片素材/Miscellaneous/kid_left" + wstring(1, L'0' + i + 1) + L"_s.png";
        wstring right_path = L"图片素材/Miscellaneous/kid_right" + wstring(1, L'0' + i + 1) + L"_s.png";
        loadimage(&playerLefts[i], left_path.c_str());
        loadimage(&playerRights[i], right_path.c_str());
    }
}

// 根据玩家的行走方向和当前动画索引绘制对应的图像
void drawPlayer(Player player, bool lastMovingLeft, int currentAnimationIndex) {

    if (!player.isdead && !player.iswin) {
        if (player.plrsize == 60) {
            // 只有当玩家未死亡时才绘制玩家图像
            if (player.isMovingLeft) {
                // 向左行走时绘制向左的图像
                putimage_alpha(static_cast<int>(player.x - 35), static_cast<int>(player.y - 31), &playerLeft[currentAnimationIndex]);
            }
            else if (player.isMovingRight) {
                // 向右行走时绘制向右的图像
                putimage_alpha(static_cast<int>(player.x), static_cast<int>(player.y - 31), &playerRight[currentAnimationIndex]);
            }
            else if (lastMovingLeft) {
                // 如果上一次移动的方向是向左，则保持向左的图像
                putimage_alpha(static_cast<int>(player.x - 35), static_cast<int>(player.y - 31), &playerLeft[currentAnimationIndex]);
            }
            else {
                // 默认情况下，保持向右的图像
                putimage_alpha(static_cast<int>(player.x), static_cast<int>(player.y - 31), &playerRight[currentAnimationIndex]);
            }
        }
        else {
            if (player.isMovingLeft) {
                putimage_alpha(static_cast<int>(player.x - 23), static_cast<int>(player.y - 20), &playerLefts[currentAnimationIndex]);
            }
            else if (player.isMovingRight) {
                putimage_alpha(static_cast<int>(player.x), static_cast<int>(player.y - 20), &playerRights[currentAnimationIndex]);
            }
            else if (lastMovingLeft) {
                putimage_alpha(static_cast<int>(player.x - 23), static_cast<int>(player.y - 20), &playerLefts[currentAnimationIndex]);
            }
            else {
                putimage_alpha(static_cast<int>(player.x), static_cast<int>(player.y - 20), &playerRights[currentAnimationIndex]);
            }
        }
    }
    else {
        // 玩家死亡时绘制死亡图像
        IMAGE deathImage;
        const wchar_t* deathImagePath = L"图片素材/Miscellaneous/banner_death.png";
        loadimage(&deathImage, deathImagePath);
        if (player.isdead) {
            // 在玩家当前位置绘制死亡图像
            putimage_alpha(static_cast<int>(player.x), static_cast<int>(player.y), &deathImage);
        }
    }
}

void updatePlayer(Player& player, GameEssentials game) {
    plrdeath(player,game);
    if (!player.isdead && !player.iswin) {
        // 只有当玩家未死亡时才更新玩家状态
        if (player.isJumping) {
            player.y -= player.velocityY;
            player.velocityY -= game.gravity;
            if (player.y >= game.window_height) {
                // 如果玩家落地
                player.y = game.window_height;
                player.velocityY = 0;
                player.isJumping = false;
                player.isOnGround = true;
                player.jumpCount = 0;  // 重置跳跃计数器
                
            }
        }
        else { // 如果玩家不在地面上，持续下落直到落地
            if (player.y < game.window_height - player.plrsize) {
                player.y += player.velocityY;
                if (player.velocityY < 10) {//防止下落速度太快
                    player.velocityY += game.gravity;
                }
                if (player.y >= game.window_height - player.plrsize) {
                    player.y = game.window_height - player.plrsize; // 确保玩家落地
                    player.isOnGround = true;
                }
            }
        }

        if (player.isMovingLeft) {
            player.x -= game.move_speed;
            if (player.x < 0) {  // 检查左边界碰撞
                player.x = 0;      // 将玩家位置限制在边界内
            }
        }
        if (player.isMovingRight) {
            player.x += game.move_speed;
            if (player.x > game.window_width - player.plrsize) {  // 检查右边界碰撞
                player.x = game.window_width - player.plrsize;  // 将玩家位置限制在边界内
            }
        }
    }
}

// 加载背景图像
void initBackgroundImage() {
    loadimage(&background, L"图片素材/Backgrounds/background_falltreeshigh_pixel.jpg");
}

// 在指定y坐标下的真随机位置生成刺
Spike* generateRandomSpike(float y, GameEssentials game) {
    // 使用真随机数生成器生成种子
    random_device rd;
    // 使用 Mersenne Twister 算法作为随机数引擎
    mt19937 gen(rd());

    // 定义随机位置的分布器
    uniform_real_distribution<float> distX(game.spike_size, static_cast<float>(game.window_width)-game.spike_size);
    // 定义随机种类的分布器
    uniform_int_distribution<int> distSpecies(1, 110);

    // 生成随机位置和随机种类
    float randomX1 = distX(gen);
    int randomSpecies = distSpecies(gen);

    // 创建新的刺节点
    Spike* newSpike = new Spike;
    newSpike->x1 = randomX1;
    newSpike->y1 = y;
    newSpike->species = randomSpecies; // 设置刺的种类为随机数值
    newSpike->eaten = false;
    newSpike->ismissioncomplete = false;
    newSpike->hasResetPosition = false;
    newSpike->next = nullptr;

    game.curspikecnt++;

    return newSpike;
}

// 添加一个新的刺到链表中
void addSpike(Spike*& head, Spike* newSpike, GameEssentials game) {
    if (game.curspikecnt <= 40) {
        if (head == nullptr) {
            head = newSpike; // 如果链表为空，则新刺成为头部
        }
        else {
            // 找到链表末尾
            Spike* current = head;
            while (current->next != nullptr) {
                current = current->next;
            }
            // 将新刺添加到链表末尾
            current->next = newSpike;
        }
    }
}

// 绘制刺
void drawSpike(const Spike* spike) {
    if (!spike->ismissioncomplete) {
        // 加载刺图像
        IMAGE spikeImage;
        const wchar_t* imagePath = nullptr;

        // 根据刺的种类加载相应的图像
        if (spike->species <= 45) {
            imagePath = L"图片素材/Spikes/spike_up.png";
        }
        else if (spike->species > 45 && spike->species < 90) {
            imagePath = L"图片素材/Spikes/spike_down.png";
        }
        else {
            if (spike->eaten) {
                return;
            }
            if (spike->species < 95) {
                imagePath = L"图片素材/Spikes/spike_poisonapple.png";
            }
            else if (spike->species <= 100) {
                imagePath = L"图片素材/Spikes/spike_poisonapple_2.png";
            }
            else if(spike->species<105){
                imagePath = L"图片素材/Spikes/spike_coin.png";
            }
            else if(spike->species<108){
                imagePath = L"图片素材/Spikes/spike_mushroom.png";
            }
            else {
                imagePath = L"图片素材/Spikes/spike_mysterybox.png";
            }
        }

        if (imagePath != nullptr) {
            loadimage(&spikeImage, imagePath);
            // 绘制刺
            putimage_alpha(static_cast<int>(spike->x1-5), static_cast<int>(spike->y1-5), &spikeImage);

        }
    }
}

// 绘制所有刺
void drawAllSpikes(Spike*& head, GameEssentials game) {
    Spike* current = head;
    Spike* prev = nullptr; // 用于保存当前节点的前一个节点，以便在释放节点后更新链表

    while (current != nullptr) {
        // 如果刺的 ismissioncomplete 属性为真，则释放该刺
        if (current->ismissioncomplete||current->eaten) {
            Spike* temp = current;
            current = current->next; // 更新当前节点
            delete temp; // 释放刺内存
            game.curspikecnt--;

            if (prev != nullptr) {
                prev->next = current; // 更新前一个节点的 next 指针，跳过已释放的节点
            } else {
                head = current; // 如果前一个节点为空，则更新头指针
            }
        } else {
            // 绘制单个刺
            drawSpike(current);
            prev = current; // 更新前一个节点为当前节点
            current = current->next; // 移动到下一个节点
        }
    }
}

//更新刺的位置
void updateSpikePositions(Spike*& head, GameEssentials game) {
    Spike* current = head;
    Spike* prev = nullptr;

    while (current != nullptr) {

        if (current->species <= 45) {
            current->y1 -= 5; // 将刺向上移动
            if (current->y1 <= 0) {
                current->ismissioncomplete = true;
            }
        }
        else if ((current->species > 45 && current->species < 90) || current->species >= 105) {
            if (!current->hasResetPosition) {
                current->y1 = 0; // 将刺位置重置为0
                current->hasResetPosition = true; // 标记为已重置位置
            }
            current->y1 += 5; // 将刺向下移动
            if (current->y1 >= game.window_height) {
                current->ismissioncomplete = true;
            }
        } else {
            current->y1 -= 5; // 跳跃介质向上移动
            if (current->y1 <= 0) {
                current->ismissioncomplete = true;
            }
        }

        // 更新前一个节点指针为当前节点
        prev = current;
        // 移动到链表的下一个节点
        current = current->next;
    }
}

//神秘盒子的效果
void triggermystery(Player& player) {
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<int> dist(1, 100);

    // 生成真随机数
    int mysteryfac = dist(gen);
    if (mysteryfac <= 10) {
        player.coins += 167;
    } else if (mysteryfac <= 27) {
        player.plrsize = 40;
    } else if (mysteryfac <= 67) {
        player.jumpCount = 0;
        player.coins += 114;
    } else if (mysteryfac <= 89) {
        player.coins += 200;
    } else {
        player.coins -= 100;
    }
}

// 碰撞检测
void checkHit(Player& player, Spike* head, GameEssentials game) {
    Spike* current = head;
    while (current != nullptr) {
        // 判断玩家与刺的碰撞
        if (player.x < current->x1 + game.spike_size &&
            player.x + player.plrsize > current->x1 &&
            player.y < current->y1 + game.spike_size &&
            player.y + player.plrsize > current->y1 && !current->eaten) {

            if (current->species < 90) {// 如果玩家与刺相交，玩家死亡
                player.isdead = true;
            }
            
            else {
                current->eaten = true;
                current->ismissioncomplete = true;
                if (current->species <= 100) {//如果吃到浆果，跳跃次数＋2
                    player.jumpCount = 0;
                    player.coins += 50;

                } else if(current->species<105){//如果吃到金币
                    player.coins += 100;
                    
                } else if(current->species < 108){//如果吃到蘑菇
                    player.coins += 137;
                    player.plrsize = 40;
                    
                } else {//如果吃到盲盒
                    triggermystery(player);                    
                }
            }
        }
        current = current->next;
    }
}

//绘制出暂停按钮
void drawPauseIcon(GameEssentials& game) {
    if (!game.isPaused) {
        IMAGE logo;
        loadimage(&logo, L"图片素材/Miscellaneous/pause_button.png");
        putimage_alpha(game.window_width - 130, 0, &logo);

        //鼠标检测是否点击按钮
        int mouseX, mouseY;
        MOUSEMSG msg;
        if (MouseHit()) {
            msg = GetMouseMsg();
            mouseX = msg.x;
            mouseY = msg.y;

            if (msg.uMsg == WM_LBUTTONDOWN) {
                if (mouseX >= game.window_width - 130 && mouseX <= game.window_width - 29 
                    && mouseY >= 0 && mouseY <= 101) {
                    game.isPaused = 1;
                }
                if (mouseX >= game.window_width - 268 && mouseX <= game.window_width - 140
                    && mouseY >= 0 && mouseY <= 101) {
                    if (game.musicplaying < 3) {
                        game.musicplaying++;
                    }
                    else {
                        game.musicplaying = 0;
                    }

                    game.playedcurBGM = 0;
                }
            }
        }
    }
}

void drawMusicButton(GameEssentials game,int factor) {
    IMAGE buttons[4];
    for (size_t i = 0; i <= 3; i++) {
        //使用拼接字符串的方法引入类似名称的图片
        wstring button_path = L"图片素材/Miscellaneous/music_button_" + wstring(1, L'0' + i) + L".png";
        loadimage(&buttons[i], button_path.c_str());
    }
    if (factor == 1) {
        putimage_alpha(game.window_width - 130, 0, &buttons[game.musicplaying]);
    }
    else {
        putimage_alpha(game.window_width - 268, 0, &buttons[game.musicplaying]);
    }
}

//播放主界面BGM
void playBGM(GameEssentials game) {
    if (game.musicplaying == 1) {
        auto musicThreadM1 = [&game]() {
            sndPlaySound(L"音频素材/BGM/Yakitori.wav", SND_FILENAME | SND_ASYNC| SND_LOOP);
            Sleep(1000000);
            PlaySound(NULL, 0, 0);
            };
        thread musicPlayThreadM1(musicThreadM1);
        musicPlayThreadM1.detach();
    }
    else if (game.musicplaying == 2) {
        auto musicThreadM2 = [&game]() {
            sndPlaySound(L"音频素材/BGM/Sky_Track.wav", SND_FILENAME | SND_ASYNC | SND_LOOP);
            Sleep(1000000);
            PlaySound(NULL, 0, 0);
            };
        thread musicPlayThreadM2(musicThreadM2);
        musicPlayThreadM2.detach();
    }
    else if (game.musicplaying == 3) {
        auto musicThreadM3 = [&game]() {
            sndPlaySound(L"音频素材/BGM/Rise.wav", SND_FILENAME | SND_ASYNC | SND_LOOP);
            Sleep(1000000);
            PlaySound(NULL, 0, 0);
            };
        thread musicPlayThreadM3(musicThreadM3);
        musicPlayThreadM3.detach();
    }
    else {
        PlaySound(NULL, 0, 0); // 停止播放当前音乐
        return; // 返回，不需要播放新的音乐
    }
}

void planecrash(GameEssentials game) {
    // 设置飞机的初始位置
    int planeX = game.window_width - 100; // 飞机起始横坐标
    int planeY = 0; // 飞机起始纵坐标

    // 加载飞机图像
    IMAGE plane;
    loadimage(&plane, L"图片素材/Miscellaneous/Opp_MK2.png");

    // 加载背景图像
    IMAGE background;
    loadimage(&background, L"图片素材/Backgrounds/background_falltreeshigh_pixel.jpg");

    // 播放音乐的线程函数
    auto musicThread1 = [&game]() {
        PlaySound(L"音频素材/sfx/mk2_flying_sfx.wav", NULL, SND_FILENAME | SND_ASYNC);
        Sleep(2900);
        // 停止音乐
        PlaySound(NULL, 0, 0);
        };

    // 在新线程中播放音乐
    thread musicPlayThread1(musicThread1);
    musicPlayThread1.detach();

    // 让飞机从右侧移动到中部
    while (planeX > (game.window_width / 2 - 50)) { // 当飞机横坐标大于窗口中心的横坐标时循环

        cleardevice();

        //引入随机,控制MK2移动速度以及振幅
        random_device rd;
        mt19937 gen(rd());
        uniform_int_distribution<int> dist1(2, 5);
        uniform_int_distribution<int> dist2(-5, 5);

        putimage(0, 0, &background);
        putimage_alpha(planeX, planeY + dist2(gen), &plane);

        // 更新飞机的横坐标，使其向左移动
        planeX -= dist1(gen);
        FlushBatchDraw();

        // 等待一段时间，控制飞机移动速度
        Sleep(10);
    }

    const wchar_t* folderPath = L"图片素材/Miscellaneous/Opp_bomb_";
    const wchar_t* fileExtension = L".png";

    auto musicThread2 = [&game]() {
        PlaySound(L"音频素材/sfx/mk2_explotion_sfx.wav", NULL, SND_FILENAME | SND_ASYNC);
        Sleep(1000);
        PlaySound(NULL, 0, 0);
        };

    thread musicPlayThread2(musicThread2);
    musicPlayThread2.detach();

    for (int i = 1; i <= 5; ++i) {
        // 拼接图片路径
        wstring imagePath = folderPath + to_wstring(i) + fileExtension;
        IMAGE bombImage;
        loadimage(&bombImage, imagePath.c_str());
        putimage_alpha((game.window_width / 2 - 50)-(i-1)*5, -(i - 1) * 12, &bombImage);
        FlushBatchDraw();
        Sleep(65);
    }
    game.isplanecrash = 1;
}

// 开始前界面
void drawStartScreen(GameEssentials& game) {
    loadanime(game); // 初始化玩家图像

    if (game.createstartscreen) {
        initgraph(game.window_width, game.window_height); // 初始化窗口大小
    }
    
    // 加载背景图片
    IMAGE background;
    const wchar_t* backgroundImagePath = L"图片素材/Backgrounds/background_dragoncastle_pixel.jpg";
    loadimage(&background, backgroundImagePath);

    // 设置背景颜色
    setbkcolor(CYAN);
    cleardevice();

    // 绘制背景图片
    putimage_alpha(0, 0, &background);

    // 绘制标题
    settextstyle(40, 0, _T("Comic Sans MS"));
    settextcolor(BLACK);
    outtextxy(40, 0, _T("I Wanna be Jack"));

    // 绘制按钮
    const wchar_t* BUTTON_TEXT[] = { L"Start Game", L"Scoreboard", L"Tutorial", L"Quit Game" };
    const int NUM_BUTTONS = sizeof(BUTTON_TEXT) / sizeof(BUTTON_TEXT[0]);
    const int BUTTON_WIDTH = 200;
    const int BUTTON_HEIGHT = 50;
    const int BUTTON_VERTICAL_MARGIN = 30;
    const int BUTTON_HORIZONTAL_OFFSET = (game.window_width - BUTTON_WIDTH) / 2;

    for (int i = 0; i < NUM_BUTTONS; ++i) {
        setfillcolor(LIGHTGRAY);
        setlinecolor(BLACK);
        fillrectangle(BUTTON_HORIZONTAL_OFFSET,
            250 + i * (BUTTON_HEIGHT + BUTTON_VERTICAL_MARGIN),
            BUTTON_HORIZONTAL_OFFSET + BUTTON_WIDTH,
            250 + i * (BUTTON_HEIGHT + BUTTON_VERTICAL_MARGIN) + BUTTON_HEIGHT);
        rectangle(BUTTON_HORIZONTAL_OFFSET,
            250 + i * (BUTTON_HEIGHT + BUTTON_VERTICAL_MARGIN),
            BUTTON_HORIZONTAL_OFFSET + BUTTON_WIDTH,
            250 + i * (BUTTON_HEIGHT + BUTTON_VERTICAL_MARGIN) + BUTTON_HEIGHT);
        settextstyle(20, 0, _T("宋体"));
        settextcolor(BLACK);
        outtextxy(BUTTON_HORIZONTAL_OFFSET + BUTTON_WIDTH / 2 - textwidth(BUTTON_TEXT[i]) / 2,
            250 + i * (BUTTON_HEIGHT + BUTTON_VERTICAL_MARGIN) + BUTTON_HEIGHT / 2 - textheight(BUTTON_TEXT[i]) / 2,
            BUTTON_TEXT[i]);
    }
}

//暂停界面
void drawPauseScreen(GameEssentials& game) {
    if (game.isPaused) {
        IMAGE logo1;
        loadimage(&logo1, L"图片素材/Backgrounds/paused_shadder.png");
        putimage_alpha(235, 174, &logo1);

        IMAGE logo2;
        loadimage(&logo2, L"图片素材/Miscellaneous/resume_button.png");
        putimage_alpha(game.window_width - 130, 0, &logo2);

        //鼠标检测是否点击按钮
        int mouseX, mouseY;
        MOUSEMSG msg;
        if (MouseHit()) {
            msg = GetMouseMsg();
            mouseX = msg.x;
            mouseY = msg.y;
            if (msg.uMsg == WM_LBUTTONDOWN) {
                if (mouseX >= game.window_width - 130 && mouseX <= game.window_width - 29
                    && mouseY >= 0 && mouseY <= 101) {
                    game.isPaused = 0;
                }
            }
        }
    }
}

void handleKeyEvents(Player& player, bool& lastMovingLeft) {
    if (GetAsyncKeyState('A') & 0x8000|| GetAsyncKeyState(VK_LBUTTON) & 0x8000) {
        player.isMovingLeft = true;
        lastMovingLeft = true;
    }else {
        player.isMovingLeft = false;
    }
    if (GetAsyncKeyState('D') & 0x8000|| GetAsyncKeyState(VK_RBUTTON) & 0x8000) {
        player.isMovingRight = true;
        lastMovingLeft = false;
    }else {
        player.isMovingRight = false;
    }
}

//绘制计时器
void drawElapsedTime(int x, int y, int elapsedTimeInSeconds) {
    settextstyle(30, 0, _T("华文隶书"));
    settextcolor(BLACK);
    elapsedTimeInSeconds -= 3;
    // 将秒数转换为分钟和秒，并格式化为字符串
    int minutes = elapsedTimeInSeconds / 60;
    int seconds = elapsedTimeInSeconds % 60;
    TCHAR timeStr[20];
    swprintf(timeStr, 20, _T("Time: %02d:%02d"), minutes, seconds);
    outtextxy(x, y, timeStr); // 在指定位置绘制文本
}

// 游戏界面
void drawGameScreen(Spike*& head, GameEssentials game) {
    Player player = { game.window_width / 2, 0,  // 设置玩家初始位置为窗口中心
                     0,
                     false,
                     false,
                     false,
                     false,
                     true,
                     0 };  // 初始设置为在地面上

    player.difficlty = getDifficulty();
    initgraph(game.window_width, game.window_height); // 初始化窗口大小

    initBackgroundImage();  // 加载背景图像

    // 记录游戏开始的时间点
    auto startTime = chrono::steady_clock::now();

    if (!game.isplanecrash) {
        planecrash(game);//调用初始坠机动画
    }

    bool lastMovingLeft = false;  // 记录上一次的移动方向

    int frameCounter = 0;  // 动画帧计时器
    int mushroomframecnt = 0;//蘑菇帧计时器

    // 背景位置
    double bgPosY = 0; // 初始化为窗口上方，使其能够向上滚动
    game.musicplaying = 0;

    while (true) {
        auto PauseBeginTime = chrono::steady_clock::now();
        
        if (!game.playedcurBGM) {
            playBGM(game);
            game.playedcurBGM = 1;
        }

        // 检查键盘输入，切换暂停状态
        if (GetAsyncKeyState('P') & 0x8000) {
            //PauseBeginTime = chrono::steady_clock::now();
            DWORD currentTime = GetTickCount(); // 获取当前系统时间
            // 如果距离上次切换暂停状态的时间超过500毫秒，则可以再次切换暂停状态
            if (currentTime - game.lastPauseToggleTime >= 500) {
                game.isPaused = !game.isPaused;
                game.lastPauseToggleTime = currentTime; // 更新上次切换暂停状态的时间
                Sleep(200); // 延迟一段时间，避免连续多次切换
            }
        }

        // 如果按下 'R' 键，关闭当前游戏窗口，并返回到开始界面
        if ((player.iswin || player.isdead) && GetAsyncKeyState('R') & 0x8000) {
            closegraph();
            resetVariables(head, game);
            drawStartScreen(game);
            return;
        }

        auto currentTime = chrono::steady_clock::now(); // 获取当前时间
        auto elapsedTime = chrono::seconds(0); // 初始化已经运行的时间为0
        auto pausedTime = chrono::seconds(0);
        bool recordedpausebegin = 0;

        if (game.isPaused) {
            if (!recordedpausebegin) {
                PauseBeginTime = chrono::steady_clock::now();
                recordedpausebegin = 1;
            }
            currentTime = chrono::steady_clock::now(); // 获取当前时间
            pausedTime = chrono::duration_cast<chrono::seconds>(currentTime - PauseBeginTime);
        }

        if (!game.isPaused) {
            recordedpausebegin = 0;
            currentTime = chrono::steady_clock::now();
            elapsedTime = chrono::duration_cast<chrono::seconds>(currentTime - startTime);

            if (player.plrsize != 60) {
                mushroomframecnt++;
                if (mushroomframecnt >= 150) {
                    mushroomframecnt = 0;
                    player.plrsize = 60;
                }
            }

            // 处理键鼠事件
            handleKeyEvents(player, lastMovingLeft);

            //刺的随机生成
            if (player.difficlty == 2) {
                if (frameCounter >= 20) { // 每30帧生成一个刺
                    Spike* newSpike = generateRandomSpike(game.window_height, game);
                    addSpike(head, newSpike, game);
                    frameCounter = 0; // 重置帧计数器
                }
            }
            else if (player.difficlty == 1) {
                if (frameCounter >= 45) { // 每45帧生成一个刺
                    Spike* newSpike = generateRandomSpike(game.window_height, game);
                    addSpike(head, newSpike, game);
                    frameCounter = 0; // 重置帧计数器
                }
            }
            else if (player.difficlty == 3) {
                if (frameCounter >= 10) { // 每20帧生成一个刺
                    Spike* newSpike = generateRandomSpike(game.window_height, game);
                    addSpike(head, newSpike, game);
                    frameCounter = 0; // 重置帧计数器
                }
            }

            if ((GetAsyncKeyState(VK_SPACE) & 0x8000|| GetAsyncKeyState(VK_MBUTTON)&0x8000) && !player.isSpacePressed &&
                (player.isOnGround || player.jumpCount < 2)) {
                // 如果在地面上或跳跃次数小于2且按下空格键且空格键之前未被按下
                player.velocityY = game.jump_speed;
                player.isJumping = true;
                player.isOnGround = false;  // 设置为不在地面上
                player.jumpCount++;         // 增加跳跃次数                
            }
            if (!(GetAsyncKeyState(VK_SPACE) & 0x8000)&&!(GetAsyncKeyState(VK_MBUTTON) & 0x8000)) {  // 如果松开空格键
                player.isSpacePressed = false;  // 设置为空格键未被按下
            }
            else {
                player.isSpacePressed = true;  // 设置为空格键被按下
            }

            updatePlayer(player, game);

            // 使玩家保持在屏幕中央
            if (player.y > (game.window_height / 2 - player.plrsize) && bgPosY >= -3120) {
                player.y = game.window_height / 2 - player.plrsize;
                // 移动背景
                moveBackground(bgPosY, player, game);
                if (head != nullptr) {
                    updateSpikePositions(head, game);
                }
            }
            if (player.y >= 740 && bgPosY <= -3120) {
                player.iswin = true;
                auto musicThreadwin = [&game]() {
                    PlaySound(L"音频素材/sfx/plr_win_sfx.wav", NULL, SND_FILENAME | SND_ASYNC);
                    Sleep(3000);
                    PlaySound(NULL, 0, 0);
                    };
                game.musicplaying = 0;
                thread musicPlayThreadwin(musicThreadwin);
                musicPlayThreadwin.detach();
            }

            if (movecnt % 50 == 0)player.coins += 5;//根据向下运动距离增加金币

            // 更新动画帧计时器
            frameCounter++;
            if (frameCounter % 8 == 0) {  //修改人物动画快慢
                game.cur_plr_anime_index++;
                game.cur_plr_anime_index %= game.plr_anime_num;  // 循环播放人物动画
            }
        }
        // 绘制背景
        drawBackground(background, bgPosY);

        // 绘制玩家
        drawPlayer(player, lastMovingLeft, game.cur_plr_anime_index);

        drawMusicButton(game,2);

        auto actualElapsedTime = elapsedTime - pausedTime;

        if (!game.isPaused) {
            // 绘制游戏已经运行的时间，仅在游戏不暂停时更新计时器
            drawElapsedTime(game.window_width/2-100, 20, static_cast<int>(actualElapsedTime.count()));
        }
     
        if (!player.isdead && !player.iswin) {
            //时刻显示金币数量
            displayCoinValue(15, 100, player, 1);
        }

        //画出是否能跳跃的icon
        drawJumpCnt(player);

        //画出暂停icon
        drawPauseIcon(game);

        if (game.isPaused && GetAsyncKeyState('L') & 0x8000) {
            closegraph();
            resetVariables(head, game);
            drawStartScreen(game);
            return;
        }

        if (head != nullptr) {
            // 绘制所有刺
            drawAllSpikes(head, game);
            //检测是否碰撞
            checkHit(player, head, game);
        }

        //绘制暂停屏幕
        drawPauseScreen(game);

        // 绘制死亡动画和横幅
        plrdeath(player,game);

        while ((player.isdead || player.iswin) && !game.namesandcoinssaved) {
            string username = getUsernameFromInput(player);
            // 检查用户名文件是否存在，如果不存在则创建新文件
            if (!checkIfUsernameExists("UserData/PlayerInfo.txt", username)) {
                saveUsernameToFile(player, username, "UserData/PlayerInfo.txt");
                game.namesandcoinssaved = 1;
            }
        }
        FlushBatchDraw();
        Sleep(1);
    }
}

// 完整流程函数
void processLeaderboard(const string& file_path) {
    // 读取用户数据
    vector<UserData> userDataVec = readUserDataFromFile(file_path);

    // 排序用户数据
    sortUserDataByCoins(userDataVec);

    // 显示排行榜
    displayLeaderboard(userDataVec);
}

//用WinMain防止产生控制台
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    GameEssentials game;

    drawStartScreen(game);//启动！！

    Spike* head = nullptr; // 刺链表的头指针，初始化工作

    //鼠标检测是否点击按钮
    int mouseX, mouseY;
    MOUSEMSG msg;

    BeginBatchDraw();//防止闪烁

    string file_path = "UserData/PlayerInfo.txt";

    while (true) {
        //绘制音乐按钮
        drawMusicButton(game,1);
        if (!game.playedcurBGM) {
            playBGM(game);
            game.playedcurBGM = 1;
        }
        if (MouseHit()) {
            msg = GetMouseMsg();
            mouseX = msg.x;
            mouseY = msg.y;
            if (msg.uMsg == WM_LBUTTONDOWN) {
                //音乐控制
                if (mouseX >= game.window_width - 130 && mouseX <= game.window_width
                    && mouseY >= 0 && mouseY <= 155) {
                    if (game.musicplaying < 3) {
                        game.musicplaying++;
                    }
                    else {
                        game.musicplaying = 0;
                    }

                    game.playedcurBGM = 0;

                    game.createstartscreen = 0;
                    drawStartScreen(game);
                    game.createstartscreen = 1;
                }
                
                if (mouseX >= (game.window_width - 200) / 2 && mouseX <= (game.window_width + 200) / 2 &&
                    mouseY >= 250 && mouseY <= 300) {
                    drawGameScreen(head,game);
                }
                else if (mouseX >= (game.window_width - 200) / 2 && mouseX <= (game.window_width + 200) / 2 &&
                    mouseY >= 330 && mouseY <= 380) {
                    processLeaderboard(file_path);
                }
                else if (mouseX >= (game.window_width - 200) / 2 && mouseX <= (game.window_width + 200) / 2 &&
                    mouseY >= 410 && mouseY <= 460) {
                    givetutorial();
                }
                else if (mouseX >= (game.window_width - 200) / 2 && mouseX <= (game.window_width + 200) / 2 &&
                    mouseY >= 490 && mouseY <= 540) {
                    // Quit Game 按钮
                    closegraph();
                    exit(0); // 结束程序
                }
            }
        }
        FlushBatchDraw();//防止闪烁
    }
    EndBatchDraw();//防止闪烁
    closegraph();

    return 0;
}
