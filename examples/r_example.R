# Train this example from the command line:
# python -m mlaunchpad -c r_example_cfg.yml -t
#
# Start REST API:
# python -m mlaunchpad -c r_example_cfg.yml -a
#
# Example API call:
# http://127.0.0.1:5000/some/v0/varieties?sepal.length=4.9&sepal.width=2.4&petal.length=3.3&petal.width=1

library(rpart)

create_trained_model <- function(model_conf, old_model=NULL) {
    # use get_dataframe(name) and put_dataframe(name) to access configured data_sources and data_sinks
    print(paste("Hello from", model_conf$name))

    df <- get_dataframe("petals")

    print("Got petals data:")
    print(head(df))

    print("Old model:")
    print(old_model)

    print("Training model:")
    tree <- rpart(variety ~ ., data = df, method = "class")

    finished_model <- list(mymodel=tree, favcolor="green")
    print(finished_model)

    return(finished_model)
}

test_trained_model <- function(model_conf, model) {
    # use get_dataframe(name) and put_dataframe(name) to access configured data_sources and data_sinks
    df <- get_dataframe("petals_test")

    print("Got petals test data:")
    print(head(df))

    print("Got model:")
    print(model)
    tree <- model$mymodel

    print("Testing model:")
    pred <- predict(tree, df, type="class")
    acc <- mean(pred == df$variety)
    metrics <- list(accuracy=acc, favoritecolor=model$favcolor)

    print("Resulting metrics:")
    print(metrics)

    return(metrics)
}

# TODO: I may have to change the name of the predict function in python for consistency...
predict_with_model <- function(model_conf, args_list, model) {
    # use get_dataframe(name) and put_dataframe(name) to access configured data_sources and data_sinks
    print("Prediction input:")
    print(args_list)

    tree <- model$mymodel

    print("Predicting with model")
    pred <- predict(tree, data.frame(args_list), type="class")

    print("Raw prediction:")
    print(pred)

    output <- list(iris_variety=pred, probability=0.9999, test="hello")

    print("Prediction output in R:")
    print(output)

    return(output)
}


# test (generic test code):
# data("iris")
# colnames(iris)[colnames(iris)=="Species"] <- "variety"
# sample <- sample.int(n = nrow(iris), size = floor(.75*nrow(iris)), replace = F)
# train <- iris[sample, ]
# test  <- iris[-sample, ]
#
# my_ds_train <- list(petals = train)
# model <- create_trained_model(0, my_ds_train, 0, 0)
# print(model)
#
# my_ds_test <- list(petals_test = test)
# output <- test_trained_model(0, my_ds_test, 0, model)
# print(output)
#
#
# args_dict = list('Sepal.Length'=4.1, 'Sepal.Width'=2.1, 'Petal.Length'=1.6, 'Petal.Width'=0.4)
# output <- predict_with_model(0, 0, 0, args_dict, model)
# print(output)
