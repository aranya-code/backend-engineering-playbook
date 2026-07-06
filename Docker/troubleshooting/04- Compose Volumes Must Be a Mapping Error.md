# `volumes must be a mapping` Error in Compose

![Volume configuration issue](../images/Volume_Issue.png)

## The Broken Compose File

```yaml
services:
  drupal:
    image: drupal
    ports:
      - "8080:80"
    volumes:
      - drupal-modules:/var/www/html/modules
      - drupal-profiles:/var/www/html/profiles
      - drupal-sites:/var/www/html/sites
      - drupal-themes:/var/www/html/themes

  postgres:
    image: postgres
    environment:
      - POSTGRES_PASSWORD=password

volumes:
  - drupal-modules:
  - drupal-profiles:
  - drupal-sites:
  - drupal-themes:
```

## Why It Happens

The error `volumes must be a mapping` happens because of how the top-level `volumes` are defined at the very end of the `docker-compose.yml` file.

In YAML, the hyphen (`-`) creates a list (or array), but Docker Compose expects top-level named volumes to be defined as a mapping (a dictionary/object).

## Corrected Code

```yaml
services:
  drupal:
    image: drupal
    ports:
      - "8080:80"
    volumes:
      - drupal-modules:/var/www/html/modules
      - drupal-profiles:/var/www/html/profiles
      - drupal-sites:/var/www/html/sites
      - drupal-themes:/var/www/html/themes

  postgres:
    image: postgres
    environment:
      - POSTGRES_PASSWORD=password

volumes:
  drupal-modules:  # Removed the hyphens here
  drupal-profiles:
  drupal-sites:
  drupal-themes:
```
