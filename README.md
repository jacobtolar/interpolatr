# interpolatr

Interpolatr is a command line tool and library for interpolating configuration
settings into templatized files. It uses the [jinja2](http://jinja.pocoo.org/docs/2.9/)
library for templating.

## Usage
The `interpolatr` command-line tool currently supports two configuration 
sources (command line and YAML; see below) and a single template sink (
file-based jinja2 templates). However, it is easy to supply your own 
configuration sources or template sinks if necessary.

Usage:

```
interpolatr [OPTIONS] [<config-class> <config-args>]... [<supplier-class> <supplier-args>]...
```

For example, using builtin config and template suppliers:

```
interpolatr -D override_setting=value YamlConfigSource --path conf.yaml  ExtensionFileSinkSupplier --target_dir root
```

### Configuration Sources
There are currently two built-in configuration sources for `interpolatr`:

1. *Command line*: You can specify configuration values when calling 
   `interpolatr` using the `-D` flag: `interpolator -D foo=bar`.

2. *YAML*: You can specify configuration values in a hierarchical `yaml` format.
    
    The format looks like this: 
    ```yaml
    settings: 
        setting_name: setting_value
        setting_two: other_value
    
    # Optional files to inherit settings from
    base: 
        - file/to/inherit-from.yml
        
        # Functionally, this is no different than flattening the list out
        - [ some/more.yaml, and-even-more.yml ]
        
        - final-base-file.yml
    ```

    These settings are populated into a `ChainedMap`, so any settings missing
    in your top-level configuration will be pulled from its parent(s).
    
It is simple to define your own configuration sources: see `config.py`. 
If using the command line, you can use a custom config source by 
specifying the fully qualified class path on the command line.

### Configuration Sinks
Configuration values can currently be written into templatized configuration 
files. The templating is powered by `jinja2`, so you may use any valid `jinja2`
expressions to define your configuration files. 

It should be straightfoward to customize this process as well; see the code in
`sink.py` for reference.

## Notes
* This was developed under Python 2.7, but at least gives the appearance 
of working under Python 3.
* This is an early version of this tool, so the interfaces are subject to 
change.


## Copyright and License
Copyright 2017, Yahoo Inc.

Licensed under the terms of the Apache License, Version 2.0.
See the LICENSE file associated with the project for terms.
