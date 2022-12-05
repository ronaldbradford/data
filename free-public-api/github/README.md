# github

## List available APIs

### Request

    curl -sL https://api.github.com/

### Response

    {
        "current_user_url": "https://api.github.com/user",
        "current_user_authorizations_html_url": "https://github.com/settings/connections/applications{/client_id}",
        "authorizations_url": "https://api.github.com/authorizations",
        "code_search_url": "https://api.github.com/search/code?q={query}{&page,per_page,sort,order}",
        "commit_search_url": "https://api.github.com/search/commits?q={query}{&page,per_page,sort,order}",
        "emails_url": "https://api.github.com/user/emails",
        "emojis_url": "https://api.github.com/emojis",
        "events_url": "https://api.github.com/events",
        "feeds_url": "https://api.github.com/feeds",
        "followers_url": "https://api.github.com/user/followers",
        "following_url": "https://api.github.com/user/following{/target}",
        "gists_url": "https://api.github.com/gists{/gist_id}",
        "hub_url": "https://api.github.com/hub",
        "issue_search_url": "https://api.github.com/search/issues?q={query}{&page,per_page,sort,order}",
        "issues_url": "https://api.github.com/issues",
        "keys_url": "https://api.github.com/user/keys",
        "label_search_url": "https://api.github.com/search/labels?q={query}&repository_id={repository_id}{&page,per_page}",
        "notifications_url": "https://api.github.com/notifications",
        "organization_url": "https://api.github.com/orgs/{org}",
        "organization_repositories_url": "https://api.github.com/orgs/{org}/repos{?type,page,per_page,sort}",
        "organization_teams_url": "https://api.github.com/orgs/{org}/teams",
        "public_gists_url": "https://api.github.com/gists/public",
        "rate_limit_url": "https://api.github.com/rate_limit",
        "repository_url": "https://api.github.com/repos/{owner}/{repo}",
        "repository_search_url": "https://api.github.com/search/repositories?q={query}{&page,per_page,sort,order}",
        "current_user_repositories_url": "https://api.github.com/user/repos{?type,page,per_page,sort}",
        "starred_url": "https://api.github.com/user/starred{/owner}{/repo}",
        "starred_gists_url": "https://api.github.com/gists/starred",
        "topic_search_url": "https://api.github.com/search/topics?q={query}{&page,per_page}",
        "user_url": "https://api.github.com/users/{user}",
        "user_organizations_url": "https://api.github.com/user/orgs",
        "user_repositories_url": "https://api.github.com/users/{user}/repos{?type,page,per_page,sort}",
        "user_search_url": "https://api.github.com/search/users?q={query}{&page,per_page,sort,order}"
    }


## List tags for a repository

### Request

    curl -s -H "Accept: application/vnd.github.v3+json" 'https://api.github.com/repos/mysql/mysql-server/tags?sort=full_name&per_page=100&page=2'


### Response (part)

    [
      {
        "name": "mysql-cluster-7.4.6",
        "zipball_url": "https://api.github.com/repos/mysql/mysql-server/zipball/refs/tags/mysql-cluster-7.4.6",
        "tarball_url": "https://api.github.com/repos/mysql/mysql-server/tarball/refs/tags/mysql-cluster-7.4.6",
        "commit": {
          "sha": "e657dfbfa8e27c30f12561c13f117fd4f1672a5e",
          "url": "https://api.github.com/repos/mysql/mysql-server/commits/e657dfbfa8e27c30f12561c13f117fd4f1672a5e"
        },
        "node_id": "MDM6UmVmMjQ0OTQwMzI6cmVmcy90YWdzL215c3FsLWNsdXN0ZXItNy40LjY="
      },
    ...

### Summary

    jq -r '.[].name' response2.json | tail

    mysql-8.0.15
    mysql-8.0.14
    mysql-8.0.13
    mysql-8.0.12
    mysql-8.0.11
    mysql-8.0.4
    mysql-8.0.3
    mysql-8.0.2
    mysql-8.0.1
    mysql-8.0.0
