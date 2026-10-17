use std::cmp::Reverse;
use std::collections::{BinaryHeap, VecDeque};

pub fn min_workers(mut jobs: Vec<Vec<i64>>) -> usize {
    jobs.sort_unstable_by_key(|job| job[0]);
    let mut heap = BinaryHeap::<Reverse<i64>>::new();
    for job in jobs {
        if heap.peek().is_some_and(|end| end.0 <= job[0]) {
            heap.pop();
        }
        heap.push(Reverse(job[1]));
    }
    heap.len()
}

pub fn min_cost_with_pass(grid: Vec<Vec<i64>>) -> i64 {
    let (m, n) = (grid.len(), grid[0].len());
    let inf = i64::MAX / 4;
    // [0]：券已经用掉；[1]：券还没用
    let mut dp = vec![vec![[inf; 2]; n]; m];
    dp[0][0] = [0, grid[0][0]];
    for i in 0..m {
        for j in 0..n {
            if i == 0 && j == 0 { continue; }
            let up = if i > 0 { dp[i - 1][j] } else { [inf; 2] };
            let left = if j > 0 { dp[i][j - 1] } else { [inf; 2] };
            let cost = grid[i][j];
            dp[i][j][0] = (up[0] + cost)
                .min(left[0] + cost)
                .min(up[1])
                .min(left[1]);
            dp[i][j][1] = up[1].min(left[1]) + cost;
        }
    }
    dp[m - 1][n - 1][0]
}

pub fn longest_stable(values: Vec<i64>, limit: i64) -> usize {
    let mut high = VecDeque::<usize>::new();
    let mut low = VecDeque::<usize>::new();
    let (mut start, mut best) = (0, 0);
    for end in 0..values.len() {
        while high.back().is_some_and(|&i| values[i] <= values[end]) {
            high.pop_back();
        }
        high.push_back(end);
        while low.back().is_some_and(|&i| values[i] >= values[end]) {
            low.pop_back();
        }
        low.push_back(end);
        while values[*high.front().unwrap()] - values[*low.front().unwrap()] > limit {
            if high.front() == Some(&start) { high.pop_front(); }
            if low.front() == Some(&start) { low.pop_front(); }
            start += 1;
        }
        best = best.max(end - start + 1);
    }
    best
}

pub fn can_split(n: usize, conflicts: Vec<Vec<usize>>) -> bool {
    let mut neighbors = vec![vec![]; n];
    for edge in conflicts {
        let (a, b) = (edge[0], edge[1]);
        neighbors[a].push(b);
        neighbors[b].push(a);
    }
    let mut group = vec![-1i8; n];
    let mut stack = Vec::new();
    for root in 0..n {
        if group[root] != -1 { continue; }
        group[root] = 0;
        stack.push(root);
        while let Some(target) = stack.pop() {
            for &neighbor in &neighbors[target] {
                if group[neighbor] == -1 {
                    group[neighbor] = 1 - group[target];
                    stack.push(neighbor);
                } else if group[neighbor] == group[target] {
                    return false;
                }
            }
        }
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;
    fn worker_oracle(jobs: &[Vec<i64>]) -> usize {
        let mut events = vec![];
        for j in jobs {
            events.push((j[0], 1i32));
            events.push((j[1], -1i32));
        }
        events.sort_unstable(); // 相同时刻先结束，后开始
        let (mut active, mut peak) = (0, 0);
        for (_, d) in events { active += d; peak = peak.max(active); }
        peak as usize
    }
    fn grid_oracle(g: &[Vec<i64>]) -> i64 {
        fn visit(g: &[Vec<i64>], i: usize, j: usize, sum: i64, largest: i64) -> i64 {
            let sum = sum + g[i][j];
            let largest = largest.max(g[i][j]);
            if i + 1 == g.len() && j + 1 == g[0].len() { return sum - largest; }
            let mut best = i64::MAX;
            if i + 1 < g.len() { best = best.min(visit(g, i + 1, j, sum, largest)); }
            if j + 1 < g[0].len() { best = best.min(visit(g, i, j + 1, sum, largest)); }
            best
        }
        visit(g, 0, 0, 0, 0)
    }
    fn stable_oracle(v: &[i64], limit: i64) -> usize {
        let mut best = 0;
        for i in 0..v.len() {
            let (mut low, mut high) = (v[i], v[i]);
            for j in i..v.len() {
                low = low.min(v[j]); high = high.max(v[j]);
                if high - low <= limit { best = best.max(j - i + 1); }
            }
        }
        best
    }
    fn group_oracle(n: usize, edges: &[Vec<usize>]) -> bool {
        (0..(1usize << n)).any(|mask| edges.iter().all(|e|
            ((mask >> e[0]) & 1) != ((mask >> e[1]) & 1)))
    }
    #[test]
    fn workers_exhaustive() {
        let mut options = vec![];
        for start in 0..5 { for end in start + 1..=5 { options.push(vec![start,end]); } }
        let mut count = 0;
        for n in 0..=3u32 {
            for mut number in 0..options.len().pow(n) {
                let mut jobs = vec![];
                for _ in 0..n {
                    jobs.push(options[number % options.len()].clone());
                    number /= options.len();
                }
                assert_eq!(min_workers(jobs.clone()), worker_oracle(&jobs));
                count += 1;
            }
        }
        println!("workers_exhaustive={count}");
        assert_eq!(count, 3616);
        assert_eq!(min_workers(vec![vec![0,1],vec![1,10],vec![2,3]]),2);
    }
    #[test]
    fn grid_exhaustive() {
        let values = [0,1,10000];
        let mut count = 0;
        for m in 1..=3 { for n in 1..=3 {
            for mut number in 0..3usize.pow((m*n) as u32) {
                let mut g = vec![vec![0;n];m];
                for row in &mut g { for value in row {
                    *value = values[number % 3]; number /= 3;
                } }
                assert_eq!(min_cost_with_pass(g.clone()), grid_oracle(&g));
                count += 1;
            }
        } }
        println!("grid_exhaustive={count}");
        assert_eq!(count, 21297);
        assert_eq!(min_cost_with_pass(vec![vec![10000;3]]),20000);
        assert_eq!(min_cost_with_pass(vec![vec![10000;12];12]),220000);
        assert_eq!(min_cost_with_pass(vec![vec![10000;500];500]),9980000);
    }
    #[test]
    fn stable_exhaustive() {
        let values = [-2,0,2];
        let mut count = 0;
        for n in 0..=8u32 {
            for mut number in 0..3usize.pow(n) {
                let mut v = vec![];
                for _ in 0..n { v.push(values[number % 3]); number /= 3; }
                for limit in 0..=4 {
                    assert_eq!(longest_stable(v.clone(),limit), stable_oracle(&v,limit));
                    count += 1;
                }
            }
        }
        println!("stable_exhaustive={count}");
        assert_eq!(count,49205);
        assert_eq!(longest_stable(vec![7;200000],0),200000);
        assert_eq!(longest_stable(vec![-1000000000,1000000000],2000000000),2);
    }
    #[test]
    fn groups_exhaustive() {
        let mut count = 0;
        for n in 1..=4 {
            let mut options = vec![];
            for a in 0..n { for b in a..n { options.push(vec![a,b]); } }
            for mask in 0..(1usize << options.len()) {
                let edges:Vec<_> = options.iter().enumerate()
                    .filter(|(i,_)| mask & (1 << i) != 0).map(|(_,e)|e.clone()).collect();
                assert_eq!(can_split(n,edges.clone()),group_oracle(n,&edges));
                count += 1;
            }
        }
        println!("groups_exhaustive={count}");
        assert_eq!(count,1098);
        assert!(can_split(3,vec![vec![0,1],vec![0,1],vec![0,1]]));
        assert!(can_split(4,vec![vec![0,1],vec![2,3],vec![0,2]]));
        assert!(!can_split(3,vec![vec![0,1],vec![1,2],vec![2,0]]));
        assert!(!can_split(1,vec![vec![0,0]]));
        assert!(can_split(5,vec![]));
        let chain=(0..99999).map(|i|vec![i,i+1]).collect();
        assert!(can_split(100000,chain));
    }
}
