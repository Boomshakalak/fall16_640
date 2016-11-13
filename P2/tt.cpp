#include <iostream>
#include <vector>
#include <cmath>
using namespace std;
// class TreeNode{
// 	public:
// 		int val;
// 		TreeNode * left, * right;
// 		TreeNode(int a){
// 			val = a;
// 			left = NULL;
// 			right = NULL;
// 		}
// };

// void dfs(vector<int> & vec, int cur, vector<bool> & visited){
// 	//vec length 6, visited length 100
// 	if(cur == 6){
// 		//get result and return
// 	}
// 	for(int i = 0 ; i < visited.size(); i++){
// 		if(visited[i]) continue;
// 		visited[i] = true;
// 		vec[cur] = i;
// 		dfs(vec, cur + 1, visited);
// 		visited[i] = false;
// 	}
// }



// void dfs(vector<int> & vec, int cur, int acc, int l){
// 	if(acc == 6){
// 		for(int i = 0; i < 6; i++)
// 			cout << vec[i] << " ";
// 		cout <<endl;
// 		return;
// 	}
// 	for(int i = cur; i <= l - 6; i++){
// 		vec[acc] = i;
// 		dfs(vec, i + 1, acc + 1, l);
// 	}
// }

// void helper(Nested & mat, vector<int> len, vector<int> & pos, int cur, int & sum){
// 	if(cur == len.length()){
// 		sum += getNum(mat, pos);
// 		return;
// 	}
// 	for(int i = 0; i < len[cur]; i++){
// 		pos[cur] = i;
// 		helper(mat, len, pos, cur + 1, sum);
// 	}
// }
// int getSum(Nested & mat, vector<int> len){
// 	int l = len.length();
// 	int sum = 0;
// 	vector<int> pos(l, 0);
// 	helper(mat, len, l, 0, sum);
// }

// // int find_triplet(vector<int> & edges){
// 	int l = edges.size();
// 	sort(edges[i].begin(), edges[i].end());
// 	int count = 0;
// 	int k;
// 	for(int i = 0; i < l - 2; i++){
// 		k = i + 2;
// 		for(int j = i + 1; j < l - 1; j++){
// 			while(edges[i] + edges[j] > edges[k]) k++;
// 			count += k - j + 1;
// 		}
// 	}
// 	return count;
// }

// void printFunction(vector<pair<int, int> > & vec, int leftmost){
// 	int l = vec.size();
// 	for(int i = 0; i < l; i++){
// 		int pos = vec[i].second;
// 		int val = vec[i].first;
// 		// cout << "pos is   " << pos << "  left most is  " << leftmost << endl;
// 		pos -= leftmost;
// 		while(pos--){
// 			// cout << pos << endl;
// 			cout << ' ';
// 		}
// 		cout << val <<endl;
// 	}
// }
// void helper(TreeNode * root, int pos, int dis, vector<pair<int, int> > & path, int leftmost){
// 	if(root == NULL) return;
// 	pair<int, int> p;
// 	p.first = root -> val;
// 	p.second = pos;
// 	path.push_back(p);
// 	if(pos < leftmost) leftmost = pos;
// 	if(root -> left == NULL && root -> right == NULL){
// 		printFunction(path, leftmost);
// 		path.pop_back();
// 		return;
// 	}
// 	if(root -> left){
// 		helper(root -> left, pos - dis, dis / 2, path, leftmost);
// 	}
// 	if(root -> right){
// 		helper(root -> right, pos + dis, dis / 2, path, leftmost);
// 	}
// 	path.pop_back();

// 	return;
// }
// int getHeight(TreeNode * root){
// 	if(root == NULL) return 0;
// 	int max = 0;
// 	int a = getHeight(root -> left);
// 	int b = getHeight(root -> right);
// 	max = a > b ? a : b;
// 	max += 1;
// 	return max;
// }
// void printTree(TreeNode * root){
// 	if(root == NULL) return;
// 	int height = getHeight(root);
// 	int dis = pow(2, height - 1);
// 	vector<pair<int, int> > path;
// 	helper(root, 0, dis, path, 0);
// }




int main(){
	// vector<int> vec(6, 0);
	// dfs(vec, 0, 0, 20);
	struct node{
		int a;
		node(){
			a = 0;
		}
	};
	node * a = new node();
	// TreeNode * root = new TreeNode(0), * a = root;
	// root -> left = new TreeNode(1);
	// root -> right = new TreeNode(2);
	// root = root -> left;
	// root -> left = new TreeNode(3);
	// root -> right = new TreeNode(4);
	// printTree(a);
}