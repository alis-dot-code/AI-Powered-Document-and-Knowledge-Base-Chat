import { NextFunction, Request, Response } from 'express'
import { AnyZodObject, ZodError } from 'zod'

export function validateRequest(schema: AnyZodObject) {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      await schema.parseAsync({
        body: req.body,
        query: req.query,
        params: req.params,
      })
      next()
    } catch (err) {
      if (err instanceof ZodError) {
        res.status(400).json({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid request data',
            fields: err.errors.map((e) => ({
              field: e.path.join('.'),
              message: e.message,
            })),
          },
        })
        return
      }
      next(err)
    }
  }
}
