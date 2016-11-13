
// #include <iostream>
// #include <string>
// #include <unordered_set>
// #include <vector>
// #include <unordered_map>
// #include <set>
// #include <stack>
// #include <map>
#include <semaphore.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>



struct Node{
    Node * up, * down, * left, * right;
    int val;
}
void generate(Node * head){
    while(head -> left) head = head -> left;
    Node * tail = head;
    while(tail -> right) tail = tail -> right;

    while(head != tail){
        if(head -> right -> left != head){
            tail -> right = head -> right -> left;
            head -> right -> left = head;
            while(tail -> right) tail = tail -> right;
        }
        if(head -> up){
            tail -> right = head -> up;
            while(tail -> right) tail = tail -> right;
            head -> up = NULL;
        }
        if(head -> down){
            tail -> right = head -> down;
            while(tail -> right) tail = tail -> right;
            head -> down = NULL;
        }
        head = head -> right;
    }
}
// using namespace std;
typedef sem_t Semaphore;

Semaphore * make_semaphore(int val){
    Semaphore * t = (Semaphore*)malloc(sizeof(Semaphore));
    if(sem_init(t, 0, val)){
        printf("hey , wrong\n");
    }
    return t;
}


double sqrt(double x){
    double start = 0, end = x;
    double err = 0.00001;
    double tmp, mid = start;
    while(start < end){
        mid = (start + end) / 2;
        tmp = mid * mid;
        if(tmp > x){
            end = mid;
        }
        else{
            if(x - tmp < err)
                break;
            start = mid;
        }
    }
    return mid;
}

template <typename T>
struct queue{
    T * data;
    int next_in, next_out;
    int length;
    Semaphore * mutex, * items;
};

template <typename T>
queue<T> * make_queue(int length){
    queue<T> * q = (queue<T> * )malloc(sizeof(queue<T>));
    q -> data = (T *)malloc(sizeof(T) * (length));
    q -> next_in = 0;
    q -> next_out = 0;
    q -> length = length;
    q -> mutex = make_semaphore(1);
    q -> items = make_semaphore(0);
    // q -> spaces = make_semaphore(length);

    return q;
}

template <typename T>
void enqueue(queue<T> * q, T newItem){
    sem_wait(q -> spaces);
    sem_wait(q -> mutex);
    //
    q -> data[q -> next_in] = newItem;
    q -> next_in++;
    if(q -> next_in == q -> length)
        q -> next_in -= q -> length;
    sem_post(q -> mutex);
    sem_post(q -> items);
}

template <typename T>
T dequeue(queue<T> * q){
    sem_wait(q -> items);
    sem_wait(q -> mutex);
    //
    T tmp = q -> data[q -> next_out];
    q -> next_out++;
    if(q -> next_out == q -> length)
        q -> next_out -= q -> length;
    sem_post(q -> mutex);
    sem_post(q -> spaces);
    return tmp;
}

int main(){
    queue<double> * q = make_queue<double>(10);
    for(int i = 0; i < 20; i++){
        double k = i;
        k = k +  2.2;
        printf("%lf\n", k);
        enqueue(q, k);
    }

    for(int i = 0; i < 10; i ++)
        printf("%f\n", dequeue(q));
    return 0;
}






int subsum(vector<int> & nums){
    int l = nums.size();
    int pre = 0;
    int cur;
    int maxval = INT_MIN;
    for(int i = 0; i < l; i++){
        cur = pre + nums[i];
        if(cur > maxval){
            maxval = cur;
        }

        if(cur < 0){
            pre = 0;
        }
        else{
            pre = cur;
        }
    }
    return maxval;
}


N numbers

int count(vector<int> & num, int target) {
    int len = num.size();
    if (len < 2) return 0;
    int count = 0;
    int l = 0, r = len - 1;
//    sort(num.begin(), num.end());
    while(l < r) {
        while(l < r && num[l] + num[r] < target) l ++;
        l --;
        if (l >= 0) {
            count += l;
        }
        r --;
    }

    while(l < r){
        if(nums[l] + nums[r] > target){
            r--;
        }
        else{
            count += l - r;
            l++;
        }
    }
    return count;
}

we just pick n^2

hash[num[i]] ++;

int count_lonely(vector<vector<int> > & image){
    if (image.size() <= 0 || image[0].size() <= 0) return 0;
    int m = image.size();
    int n = image[0].size();
    vector<int> sumrow(m, 0);
    vector<int> sumcol(n, 0);
    for (int i = 0; i < m; i ++) {
        for (int j = 0; j < n; j ++) {
            sumrow[i] += image[i][j];
            sumcol[j] += image[i][j];
        }
    }
    int count = 0;
    for (int i = 0; i < m; i ++) {
        for (int j = 0; j < n; j ++) {
            if (image[i][j] == 1 && sumrow[i] == 1 && sumcol[j] == 1) count ++;
        }
    }
    return count;
}


vector<int> generate(vector<double> prob, int N){
    vector<int> res(N);
    int l = prob.size();
    int pos =0;
    for(int i = 0; i < l; i++){
        int m = prob[i] * N;
        for(int j = pos; j < pos + m; j++){
            res[j] = i;
        }
        pos += m;
    }
    srand(time(NULL));
    return shuffle(res);
}

vector<int> shuffle(vector<int> array){
    int l = array.size();
    for(int i = l - 1; i >= 0; i++){
        int z = rand() % (i + 1);
        int tmp = array[i];
        array[i] = array[z];
        array[z] = tmp;
        // 1 / (n - 1) to choose from 0 to l - 2,  prob (n - 1) / n
        // 1 / n , l - 2  1 / n  to  l - 1,  i = l - 1 , l  -2   1/ n
        //after[i] has a probability of 1 / n to choose any one in array
        //random number within [0, i], z
        //swap array[z] and array[i]
        // probability to choose 0 - [l - 1] are all 1 / n
        //index = l - 1 is ok
        //index = l - 2  1 / (n - 1),
        
    }
}


bool issymmeric(string str){
    int l = str.length();
    map<char, char> m;
    m['5'] = '2';
    m['6'] = '9';
    m['8'] = '8';
    m['0'] = '0';
    m['9'] = '6';
    m['2'] = '5';
    int start = 0, end = l - 1;
    char front, back;
    while(start < end){
        front = str[start];
        back = str[end];
        if(m.count(front) == 0 || m.count(back) == 0) return false;
        if(m[front] == back && m[back] == front){
            start++;
            end--;
        }
        else return false;
    }
    if(start == end){
        if(!(m[str[start]] == '0' || m[str[start]] == '8')) return false;
    }
    return true;
}

1 
{0, 8}
2 {}

// 8  0 
// 69  96 25  52  88 00
// 1 -> 3
// 2 -> 4
// 3 -> 5

vector<string> func(int N){
    bool isOdd = (n & 1);
    vector<string> one = {"0", "8"};
    vector<string> res;
    vector<string> nextOne, nextTwo;
    map<char, char> m;
    m['5'] = '2';
    m['6'] = '9';
    m['8'] = '8';
    m['0'] = '0';
    m['9'] = '6';
    m['2'] = '5';

    vector<string> two;
    string empty = "", tmp = "";
    for(char ele : m){
        tmp = ele + m[ele];
        two.push_back(tmp);
    }
    for(string ele : one)
        res.push_back(ele);
    for(string ele : two)
        res.push_back(ele);

    int pre;
    for(int i = 3 ; i <= N; i++){
        pre = i - 1;
        if(pre & 1){
            for(string ele : one){
                for(char addon : m){
                    tmp = addon + ele + m[addon];
                    nextOne.push_back(tmp);
                    res.push_back(tmp);
                }
            }
            one = nextOne;
            nextOne.clear();
        }
        else{
            for(string ele : two){
                for(char addon : m){
                    tmp = addon + ele + m[addon];
                    nextTwo.push_back(tmp);
                    res.push_back(tmp);
                }
            }
            two = nextTwo;
            nextTwo.clear();
        }
    }

    return res;



}